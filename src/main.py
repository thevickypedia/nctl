import logging
import subprocess
from multiprocessing import Process

from .cloudfront import CloudFront
from .settings import env, LOGGER

cloud_front = CloudFront()
status = {'cloudfront_process': None}


def secondary(public_url):
    if env.distribution_id:
        process = Process(target=cloud_front.update_distribution, kwargs={"origin_name": public_url.lstrip('https://')})
        process.name = "CloudfrontUpdate"
    else:
        # todo: Need to nest into the config file to update the public_url
        process = Process(target=cloud_front.create_distribution, kwargs={"filename": env.distribution_config})
        process.name = "CloudfrontCreate"
    process.start()
    LOGGER.info(f'Tunneling http://{env.host}:{env.port} through the public URL: {public_url}')
    return process


def poll(frame: str):
    try:
        level = frame.split('lvl=')[1].split()[0]
    except IndexError:
        print(frame)
        return
    if level == 'info':
        log = LOGGER.info
    elif level == 'warn':
        log = LOGGER.warning
    elif level in ('err', 'error'):
        log = LOGGER.error
    else:
        return
    msg = frame.split('msg=')[-1].replace('"', '').replace("'", "")
    if "url=" in msg and not status['cloudfront_process']:
        public_url = msg.split('url=')[-1].strip()
        status['cloudfront_process'] = secondary(public_url)
    log(msg)


def tunnel() -> None:
    # https://ngrok.com/docs/agent/config/
    command = f'ngrok http {env.port} --log "stdout"'
    if env.ngrok_config:
        command += f' --config {env.ngrok_config}'
    process = subprocess.Popen(command,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    while True:
        try:
            output = process.stdout.readline().decode().strip()
            if process.poll() and not output:
                break
            poll(output)
        except KeyboardInterrupt:
            LOGGER.warning("Tunneling interrupted")
            if status['cloudfront_process']:
                status['cloudfront_process'].join(timeout=3)
                status['cloudfront_process'].terminate()
            break
    process.kill()
    LOGGER.warning("Connection closed")
