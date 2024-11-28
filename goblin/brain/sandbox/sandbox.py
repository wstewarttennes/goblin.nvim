import docker
import os


# This is used to run arbitrary code in an insolated environment.

def run_code_in_sandbox(app_directory, dockerfile_path):
    # Initialize the Docker client
    client = docker.from_env()

    # Build the sandbox image from the Dockerfile
    sandbox_image, _ = client.images.build(
        path=app_directory,  # Directory where your Dockerfile is located
        dockerfile=dockerfile_path, 
        tag="sandbox-app"
    )

    # Create and run the sandbox container
    sandbox_container = client.containers.run(
        sandbox_image,
        detach=True,
        tty=True,
        remove=True,
        volumes={
            os.path.abspath(app_directory): {'bind': '/sandbox/app', 'mode': 'rw'},
            '/path/to/shared/logs': {'bind': '/sandbox/logs', 'mode': 'rw'}
        },
        command='/bin/sh -c "cd /sandbox/app && ./run_my_code.sh > /sandbox/logs/app.log"'
    )

    # Wait for the container to finish running
    sandbox_container.wait()

    # Capture and return the logs
    logs = sandbox_container.logs().decode('utf-8')

    return logs

