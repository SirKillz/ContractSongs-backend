import boto3
import subprocess
import os

# Configuration
function_name = 'lambda-function-name'
repository_uri = 'ecr-repository-uri'
region = 'us-east-1'
image_tag = 'latest'

# Build Docker Image
def build_docker_image(tag):
    """
    A function to build a Docker image using the provided tag.
    Disables BuildKit so the image is pushed using Docker's v2 schema 
    (rather than the OCI image index).
    """
    # Merge in the system's current environment variables,
    # plus DOCKER_BUILDKIT=0
    build_env = os.environ.copy()
    build_env["DOCKER_BUILDKIT"] = "0"

    result = subprocess.run(
        ['docker', 'build', '--platform', 'linux/amd64', '-t', tag, '.'],
        capture_output=True, text=True, env=build_env
    )
    if result.returncode != 0:
        print(f"Error building Docker image: {result.stderr}")
        exit(1)
    else:
        print(f"Docker image built successfully: {result.stdout}")

# Authenticate with ECR
def authenticate_ecr(region):
    """
    A function to authenticate with Amazon ECR using the provided region.
    
    Parameters:
        region (str): The AWS region to authenticate with.

    Returns:
        None
    """
    result = subprocess.run(['aws', 'ecr', 'get-login-password', '--region', region], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting ECR login password: {result.stderr}")
        exit(1)
    login_password = result.stdout.strip()
    result = subprocess.run(['docker', 'login', '--username', 'AWS', '--password-stdin', repository_uri], input=login_password, text=True)
    if result.returncode != 0:
        print(f"Error logging into ECR: {result.stderr}")
        exit(1)
    else:
        print(f"Logged into ECR successfully: {result.stdout}")

# Tag Docker Image
def tag_docker_image(image_id, repository_uri, tag):
    """
    A function to tag a Docker image with the provided image ID, repository URI, and tag.

    Parameters:
        image_id (str): The ID of the image to tag.
        repository_uri (str): The URI of the repository where the image will be tagged.
        tag (str): The tag to assign to the Docker image.

    Returns:
        None
    """
    result = subprocess.run(['docker', 'tag', image_id, f"{repository_uri}:{tag}"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error tagging Docker image: {result.stderr}")
        exit(1)
    else:
        print(f"Docker image tagged successfully: {result.stdout}")

# Push Docker Image to ECR
def push_docker_image(repository_uri, tag):
    """
    A function to push a Docker image to the repository URI with the specified tag.

    Parameters:
        repository_uri (str): The URI of the repository where the image will be pushed.
        tag (str): The tag associated with the Docker image.

    Returns:
        None
    """
    result = subprocess.run(['docker', 'push', f"{repository_uri}:{tag}"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error pushing Docker image: {result.stderr}")
        exit(1)
    else:
        print(f"Docker image pushed successfully: {result.stdout}")

# Update Lambda Function with New Image
def update_lambda_function_image(function_name, repository_uri, tag):
    """
    Updates the image of a Lambda function with the specified function name, repository URI, and tag.

    Args:
        function_name (str): The name of the Lambda function to update.
        repository_uri (str): The URI of the repository where the image is located.
        tag (str): The tag associated with the Docker image.

    Returns:
        dict: The response from the Lambda service after updating the function code.
    """
    lambda_client = boto3.client('lambda')
    response = lambda_client.update_function_code(
        FunctionName=function_name,
        ImageUri=f"{repository_uri}:{tag}",
        Publish=True
    )
    return response

# Main Script
if __name__ == "__main__":
    # Step 1: Build the Docker image
    build_docker_image(function_name)

    # Step 2: Authenticate Docker with ECR
    authenticate_ecr(region)

    # Step 3: Tag the Docker image
    tag_docker_image(function_name, repository_uri, image_tag)

    # Step 4: Push the Docker image to ECR
    push_docker_image(repository_uri, image_tag)

    # Step 5: Update the Lambda function
    response = update_lambda_function_image(function_name, repository_uri, image_tag)
    print(f"Updated Lambda function: {response['FunctionArn']}")
