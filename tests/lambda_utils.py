from typing import Literal
import boto3
from time import sleep
import json
import os
import subprocess
import sys
import uuid

from base64 import b64encode

LambdaType = Literal["ZIP", "DOCKER"]

LAMBDA = boto3.client('lambda')

ecr_client = boto3.client("ecr")

ACCOUNT_ID = "787991150675"

def get_image_uri(function_name: str, prefix=""):
    account_uri = f"{ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com"
    return f"{account_uri}/{function_name.lower()}:{prefix}"


def ecr_repository_exists(name: str):
    result = True
    try:
        res = ecr_client.describe_repositories(
            repositoryNames=[
                name,
            ]
        )
    except Exception as exc:
        result = False
    
    return result


def create_repository(name: str):
    return ecr_client.create_repository(
        repositoryName=name,
        imageTagMutability="MUTABLE",
        encryptionConfiguration={
            "encryptionType": "AES256",
        },
    )


def upload_image(rep_id, name: str, manifest):
    return ecr_client.put_image(
        repositoryName=name,
        imageTag="latest",
    )


def generate_docker_file(req_file_loc: str, zip_name: str, docker_runtime: str):
    return f"""
        FROM public.ecr.aws/lambda/python:3.{docker_runtime}

        COPY {req_file_loc} ${{LAMBDA_TASK_ROOT}}

        RUN pip install -r requirements.txt

        COPY {zip_name}/ ${{LAMBDA_TASK_ROOT}}

        CMD [ "lambda_function.lambda_handler" ]
        """

def create_files_dir(zip_loc: str):
    zip_name = zip_loc.removesuffix(".zip")
    subprocess.run(["unzip", "-o", zip_loc, "-d", zip_name])
    return zip_name

def create_docker_file(docker_file: str):
    with open("Dockerfile", "w") as f:
        f.write(docker_file)


def deploy_image(function_name: str, prefix: str, image_uri: str):

    os.system(f"aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com")

    subprocess.call([
        "docker", "tag", f"{function_name}:{prefix}", image_uri
    ])

    subprocess.call(["docker", "push", image_uri])


def process_docker_image(
    function_name: str, prefix: str, req_file_loc: str, zip_location: str, docker_runtime: str
):
    repo_func_name = function_name.lower()
    image_name = f"{repo_func_name}:{prefix}"
    zip_name = create_files_dir(zip_location)
    docker_file = generate_docker_file(req_file_loc, zip_name, docker_runtime)

    create_docker_file(docker_file)

    subprocess.run(
        [
            "docker",
            "build",
            "--platform",
            "linux/amd64",
            "-t",
            image_name,
            ".",
        ]
    )

    repo_exists = ecr_repository_exists(repo_func_name)
    if not repo_exists:
        create_repository(repo_func_name)

    image_uri = get_image_uri(repo_func_name, prefix)

    deploy_image(repo_func_name, prefix, image_uri)

    return image_uri

def create_client_resource(aws_account=None, region='us-east-1'):
    if not aws_account:
        if region == 'us-east-1':
            return LAMBDA
        else:
            return boto3.client('lambda', region_name=region)
    else:
        try:
            client = boto3.client('lambda',
                                  region_name=region,
                                  aws_access_key_id=aws_account['AccessKeyId'],
                                  aws_secret_access_key=aws_account['SecretAccessKey'],
                                  aws_session_token=aws_account['SessionToken'])
            return client
        except Exception as e:
            print(aws_account)
            print('Unable to get a new connection for the provided credentials' + str(e))
            return None


def get_connection(client):
    if client:
        return client
    else:
        return LAMBDA


def get_zip_file_name(input_dir, function):
    return input_dir + function + ".zip"


def get_zipfile_bytes(function, input_dir):
    zip_file_name = get_zip_file_name(input_dir, function)
    with open(zip_file_name, "rb") as data:
        return data.read()


def create_prediction_lambda(name, code_bucket, code_key,
                             model_bucket, model_key, client=None):
    client = get_connection(client)
    code = {'S3Bucket': code_bucket, 'S3Key': code_key}

    """
        # Environment paramter is of the following format
        "Environment": {
            "Variables": {
                "string" : "string"
            }
        }
   """
    environment = {}
    env_variable = {}
    env_variable['bucket'] = model_bucket
    env_variable['key'] = model_key
    environment['Variables'] = env_variable

    # TODO: check and create function
    try:
        response = client.delete_function(FunctionName=name)
    except:
        pass

    response = client.create_function(FunctionName=name,
                                      Runtime='python3.12',
                                      Role='arn:aws:iam::787991150675:role/NavigatorBot',
                                      Handler='null_model.lambda_handler',
                                      Code=code,
                                      Description='Prediction function',
                                      Environment=environment)
    resp_metadata = response['ResponseMetadata']
    status_code = resp_metadata['HTTPStatusCode']
    function_arn = response['FunctionArn']

    #print('FunctionArn: {}'.format(function_arn))
    return response


def add_permission(function_name,
                   principal,
                   source_arn,
                   action='lambda:InvokeFunction',
                   statement_id=None,
                   client=None):
    client = get_connection(client)
    if not statement_id:
        statement_id = function_name + 'statement1'
    try:
        # Trying to remove the existing permission if it exists
        response = client.remove_permission(FunctionName=function_name,
                                            StatementId=statement_id)
    except:
        pass
    response = client.add_permission(FunctionName=function_name,
                                     StatementId=statement_id,
                                     Action=action,
                                     Principal=principal,
                                     SourceArn=source_arn)
    return response


def add_permission_for_apigateway(rest_api, lambda_uri, http_method='POST',
                                  client=None, region='us-east-1', account='787991150675'):
    # TODO: get this function name from the configuration or events
    # TODO: Make statements id specific to /client/AIservice
    client = get_connection(client)
    rest_api_id = rest_api['id']
    statement_id = rest_api_id + '_' + http_method
    # print('Statement Id: {}'.format(statement_id))
    base_arn = 'arn:aws:execute-api:' + region + ':' + account + ':'
    source_arn = base_arn+rest_api_id+'/*/'+http_method+rest_api['currentPath']
    # print('SourceArn: {}'.format(source_arn))
    action = 'lambda:InvokeFunction'
    principal = 'apigateway.amazonaws.com'
    response = add_permission(lambda_uri,
                              principal,
                              source_arn,
                              action,
                              statement_id,
                              client)
    return response


def add_event_rule(event_rule, overwrite_event, function_name, function_arn):
    event_client = boto3.client('events')
    try:
        response = event_client.list_targets_by_rule(Rule=event_rule)
    except Exception as e:
        message = "Eventbridge rule {} not found! Error: ".format(event_rule) + str(e)
        print(message)
        return None

    if "Targets" in response and overwrite_event:
        targets = response["Targets"]
        if targets:
            targets = [target["Id"] for target in targets]
            try:
                response = event_client.remove_targets(
                    Rule=event_rule, Ids=targets)
            except Exception as e:
                message = "Unable to remove targets of {}. Error: ".format(event_rule) + str(e)
                print(message)

    try:
        response = event_client.put_targets(Rule=event_rule, Targets=[{'Id': function_name, 'Arn': function_arn}])
    except Exception as e:
        message = "Unable to add target for {}. Error: ".format(function_name) + str(e)
        print(message)
        response = None

    return response


def update_function_code(name, s3_bucket, s3_key, zipfile=None, client=None):
    response = None
    try:
        client = get_connection(client)
        if zipfile:
            response = client.update_function_code(FunctionName=name,
                                                ZipFile=zipfile)
        else:
            response = client.update_function_code(FunctionName=name,
                                                S3Bucket=s3_bucket,
                                                S3Key=s3_key)
        #print('Response update_function_code: {}'.format(response))
    except Exception as err:
        print('Unable to update function code! Error: ', str(err))
        raise
    return response

def update_function_configuration(name, environment, handler, layers, client=None, runtime=None):
    response = None
    kwargs = {
        'FunctionName': name,
        'Environment': environment,
        'Handler': handler,
        'Layers': layers
    }
    if runtime:
        kwargs['Runtime'] = runtime
    response = None
    try:
        MAX_RETRIES = 10
        retries = 0
        while not response and retries < MAX_RETRIES:
            timeout = 4**retries
            if retries:
                sleep(timeout)
            try:
                response = client.update_function_configuration(**kwargs)
            except client.exceptions.ResourceConflictException as err:
                print(' Warning: ', str(err))
                response = None
                retries += 1
                print('pausing execution for {} seconds'.format(timeout))
                sleep(timeout)
            except Exception as e:
                print('Error during Lambda function configuration update of {}. Error:'.format(name), str(e))
                return None
    except Exception as err:
        print('Unable to update function configuration! Error: ', str(err))
        print('Unable to update function configuration for {}! Error: '.format(name), str(err))
    return response


def is_lambda_defined(function, client=None):
    result = False
    client = get_connection(client)
    try:
        response = client.get_function(FunctionName=function)
        # print(response)
        metadata = response['ResponseMetadata']
        if metadata['HTTPStatusCode'] == 200 and response['Configuration']:
            if response['Configuration']['FunctionName'] == function:
                result = True
    except:
        pass
    return result


def get_function_info(function, client):
    client = get_connection(client)
    try:
        response = client.get_function(FunctionName=function)
        return response
    except:
        print('Unable to get the function {} details!'.format(function))
        return None


def delete_lambda(function, client=None):
    result = False
    client = get_connection(client)
    try:
        response = client.delete_function(FunctionName=function)
        # print(response)
        metadata = response['ResponseMetadata']
        if metadata['HTTPStatusCode'] == 200 or metadata['HTTPStatusCode'] == 204:
            # TODO: verify the results of the lambda delete response for function name
            result = True
    except Exception as e:
        print('Unable to delete lambda {}'.format(function) + str(e))
    return result

def get_function_configuration(function, client=None):
    response = None
    client = get_connection(client)
    try:
        response = client.get_function_configuration(FunctionName=function)
    except Exception as e:
        print('Unable to get lambda configuration {}'.format(function) + str(e))
    return response


def create_lambda(function, mappings, config, client=None, *, lambda_type="ZIP", base_function_name=""):
    output_dir = ''
    client = get_connection(client)
    try:
        # input_dir = config['inputDir']
        runtime = config['runtime']
        role = config['role']
        handler = config['handler']
        timeout = config['timeout']
        memory = config['memory']
        code_type = config['codeSource']
        output_dir = config['outputDir']
    except Exception as e:
        pass

    try:
        aws_account = config['aws_account']
    except:
        aws_account = False

    try:
        add_vpc = bool(mappings['vpc'])
        vpc_config = config['vpcConfig']
    except:
        add_vpc = False
        vpc_config = {}

    try:
        layers = mappings['layers']
    except:
        layers = []

    try:
        filesystem_configs = mappings['fileSystemConfigs']
    except:
        filesystem_configs = []

    try:
        permissions = mappings['permissions']
        prefix = config['functionNamePrefix']
        if 'sourceArn' in permissions and 'FN_NAME_PREFIX' in permissions['sourceArn']:
            permissions['sourceArn'] = permissions['sourceArn'].replace('FN_NAME_PREFIX', prefix)
    except:
        permissions = []

    try:
        environment = mappings['environment']
        try:
            # Special case: we add the function prefix to help lambda call other lambdas
            if 'FN_NAME_PREFIX' in environment['Variables'].keys():
                fn_name_prefix = config['functionNamePrefix']
                environment['Variables']['FN_NAME_PREFIX'] = fn_name_prefix
        except:
            pass
        try:
            # Special case: we add the database suffix to help use private db
            if 'DB_NAME_SUFFIX' in environment['Variables'].keys():
                db_name_suffix = config['databaseNameSuffix']
                environment['Variables']['DB_NAME_SUFFIX'] = db_name_suffix
        except:
            pass
    except:
        environment = {}

    try:
        event_rule = mappings["eventRule"]
        overwrite_event = mappings["overwriteEvent"]
        if "production" not in prefix.lower():
            event_rule = None
    except:
        event_rule = None

    try:
        req_file_loc = mappings["requirementsLocation"]
    except:
        req_file_loc = None

    image_uri = None

    try:
        if aws_account:
            # For connected accounts we need to download the code locally
            # They upload it via zip bytes
            uuid_str = str(uuid.uuid4())
            temp_zip_loc = '/tmp/' + uuid_str + '.zip'
            print(temp_zip_loc)
            if os.path.exists(temp_zip_loc):
                os.remove(temp_zip_loc)
            # Download the predict zip file
            # NOTE: this is the code from the pyxeda account
            s3_client = boto3.client('s3')
            s3_client.download_file(mappings['code']['S3Bucket'],
                                    mappings['code']['S3Key'],
                                    temp_zip_loc)
            # get_zipfile_bytes constructs the file differently
            code = {'ZipFile': get_zipfile_bytes(uuid_str, '/tmp/')}
            os.remove(temp_zip_loc)
        elif lambda_type == "DOCKER":
            docker_runtime = "12"
            try:
                docker_runtime = runtime.split(".")[1]
            except:
                pass

            image_uri = process_docker_image(base_function_name, config['functionNamePrefix'], req_file_loc , get_zip_file_name(output_dir, function), docker_runtime)
        else:
            if code_type == 'local':
                if 'code' in mappings and 'localFile' in mappings['code']:
                    code = {'ZipFile': get_zipfile_bytes(mappings['code']['localFile'], output_dir)}
                else:
                    code = {'ZipFile': get_zipfile_bytes(function, output_dir)}
            elif code_type == 's3':
                code = mappings['code']
            else:
                print('unsupported code type: {}'.format(code_type))
                code = {}
                return False
    except Exception as e:
        print('Error: ', str(e))
        pass

    retries = 0
    max_retries = 5
    response = None
    while retries < max_retries:
        try:
            if lambda_type == "DOCKER":
                response = client.create_function(FunctionName=function,
                                            Role=role,
                                            Code={"ImageUri": image_uri},
                                            PackageType='Image',
                                            Timeout=timeout,
                                            MemorySize=memory,
                                            VpcConfig=vpc_config,
                                            FileSystemConfigs=filesystem_configs,
                                            Environment=environment)
                print(response)
                break
            else:
                response = client.create_function(FunctionName=function,
                                                Runtime=runtime,
                                                Role=role,
                                                Handler=handler,
                                                Code=code,
                                                Timeout=timeout,
                                                MemorySize=memory,
                                                VpcConfig=vpc_config,
                                                FileSystemConfigs=filesystem_configs,
                                                Environment=environment,
                                                Layers=layers)
                print(response)
                break

        except Exception as e:
            if 'TooManyRequestsException' in str(e):
                print(f"TooManyRequestsException: {str(e)}. Retrying with exponential backoff...")
                retries += 1
                backoff = 2**retries
                print(f'Attempting retry: {retries}, Retrying in {backoff}s......')
                sleep(backoff)    
                
            else:
                print('Unable to create lambda: {}. Error: {}'.format(function, str(e)))
                return e 
        
    if not response:
        message = "Max retries exceeded. Could not create Lambda function."
        print(message)
        return message
        
    try:
        metadata = response['ResponseMetadata']
        if metadata['HTTPStatusCode'] == 201 and response['FunctionName'] == function:
            #print('Successfully created the lambda function: {} Arn: {}'.format(function, response['FunctionArn']))
            function_arn = response["FunctionArn"]
        else:
            print('Unable to create function: {} Response: {}'.format(function, response))
            return False
    except:
        return False
    if permissions:
        response = add_permission(function,
                                  permissions['principal'],
                                  permissions['sourceArn'],
                                  client=client)

    if event_rule:
        add_event_rule(event_rule, overwrite_event, function, function_arn)

    return response


def update_lambda(function, input_dir):
    zip_file_name = input_dir + function + ".zip"
    # print('Updating lambda function in AWS: {}'.format(zip_file_name))
    # TODO: Need to fix this for 3rd party AWS account
    function_arn = 'arn:aws:lambda:us-east-1:787991150675:function:'+function
    command = "aws lambda update-function-code --function-name " + function_arn + " --zip-file fileb://" + zip_file_name
    # print(command)
    os.system(command + ">> out.txt")
    return


def update_lambda_code(function: str, output_dir: str, lambda_type: LambdaType, client=None):

    client = get_connection(client)

    zip_file = get_zipfile_bytes(function, output_dir)

    params = {
        "FunctionName": function,
        "ZipFile": zip_file,
        "Architectures": ["x86_64"],
    }
    
    # if lambda_type == "DOCKER":
    #     docker_uri = get_image_uri()
    #     "ImageUri": "string",


    try:
        client.update_function_code(
            FunctionName=function,
            ZipFile=zip_file,
            # ImageUri="string",
            Architectures=["x86_64"],
        )
    except Exception as exc:
        print(f"Failed to deploy {exc}")


def insert_into_db(function_name, params, invocation_type='RequestResponse'):
    body = {}
    for key, param in params.items():
        print(key, param)
        body[key] = param
    log_type = 'None'
    payload = {}
    payload['httpMethod'] = 'POST'

    payload['body'] = json.dumps(body)
    print('Payload: {}'.format(json.dumps(payload)))

    response = LAMBDA.invoke(FunctionName=function_name,
                             InvocationType=invocation_type,
                             LogType=log_type,
                             Payload=json.dumps(payload))
    # print(response)
    string_response = response['Payload'].read().decode('utf-8')
    if invocation_type == 'RequestResponse':
        parsed_response = json.loads(string_response)['body']
    else:
        parsed_response = string_response
    # print("Lambda invocation message:", parsed_response)

    # TODO: handle errors properly

    return parsed_response

def update_db_entry(function_name, primary_key_params, body_params):
    query_string_params = {}
    for key, param in primary_key_params.items():
        print(key, param)
        query_string_params[key] = param
    # Setup the update params
    body = {}
    for key, param in body_params.items():
        print(key, param)
        body[key] = param
    invocation_type = 'RequestResponse'
    log_type = 'None'
    payload = {}
    payload['httpMethod'] = 'PATCH'
    payload['queryStringParameters'] = query_string_params
    payload['body'] = json.dumps(body)
    print('Payload: {}'.format(json.dumps(payload)))

    response = LAMBDA.invoke(FunctionName=function_name,
                             InvocationType=invocation_type,
                             LogType=log_type,
                             Payload=json.dumps(payload))
    # print(response)
    string_response = response["Payload"].read().decode('utf-8')
    try:
        parsed_response = json.loads(string_response)['body']
    except:
        parsed_response = string_response
    # print("Lambda invocation message:", parsed_response)

    # TODO: handle errors properly

    return parsed_response


def invoke_lambda(function_name,
                  body='',
                  query_string_params='',
                  invocation_type='RequestResponse',
                  client_context='',
                  http_method='POST',
                  client=None,
                  path=None):
    if not client:
        client = LAMBDA
    payload = {
        'body': body,
        'queryStringParameters': query_string_params,
        'httpMethod': http_method
    }
    if path:
        payload['path'] = path
    print(function_name, json.dumps(payload), invocation_type)
    try:
        response = client.invoke(FunctionName=function_name,
                             InvocationType=invocation_type,
                             LogType='Tail',
                             Payload=json.dumps(payload))
        if invocation_type == 'RequestResponse':
            response_payload = json.loads(response['Payload'].read().decode("utf-8"))
            print ("response_payload: {}".format(response_payload))
            return response_payload
        else:
            return response
    except Exception as e:
        print('Error: ', str(e))
        return None


def publish_layer_version(client, layer_name, description, content, run_times=['python3.8'], license_info='MIT'):
    try:
        response = client.publish_layer_version(LayerName=layer_name,
                                                Description=description,
                                                Content=content,
                                                CompatibleRuntimes=run_times,
                                                LicenseInfo=license_info)
        print('Response: ', response)
    except Exception as e:
        print('Unable to publish a layer {} version! Error: {}'.format(layer_name, str(e)))
        respoonse = None
    return response

def list_layers(client, compatible_runtime='python3.12', marker=None, max_items=None):
    kwargs = {
        'CompatibleRuntime': compatible_runtime
    }
    if marker:
        kwargs['Marker'] = marker
    if max_items:
        kwargs['MaxItems'] = max_items
    response = None
    try:
        response = client.list_layers(**kwargs)
        print(response)
    except Exception as e:
        print('Unale to list the layers! Error: ', str(e))
    return response

def list_layer_versions(client, layer_name, compatible_runtime='python3.12', marker=None, max_items=None):
    kwargs = {
        'CompatibleRuntime': compatible_runtime,
        'LayerName': layer_name
    }
    if marker:
        kwargs['Marker'] = marker
    if max_items:
        kwargs['MaxItems'] = max_items
    response = None

    try:
        response = client.list_layer_versions(**kwargs)
        print(response)
    except Exception as e:
        print('Unale to list the layer versions! Error: ', str(e))
    return response

def list_functions(client, marker=None, max_items=None):
    kwargs = {}
    if marker:
        kwargs['Marker'] = marker
    if max_items:
        kwargs['MaxItems'] = max_items
    response = None
    try:
        response = client.list_functions(**kwargs)
        print(response)
    except Exception as e:
        print('Unale to list the functions! Error: ', str(e))
    return response
