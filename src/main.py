import logging
import subprocess
from multiprocessing import Process

from .cloudfront import CloudFront
from .settings import env

LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(logging.StreamHandler())
LOGGER.setLevel(logging.DEBUG)

cloud_front = CloudFront()
status = {'initiated': False}


def secondary(public_url):
    # todo: setup secondary function as a Process and kill it when KeyboardInterrupt is experienced
    Process(target=cloud_front.update_distribution, kwargs={"origin_name": public_url.lstrip('https://')}).start()
    LOGGER.info(f'Tunneling http://{env.host}:{env.port} through the public URL: {public_url}')


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
    if "url=" in msg and not status['initiated']:
        public_url = msg.split('url=')[-1].strip()
        status['initiated'] = True
        secondary(public_url)
    log(msg)


def tunnel() -> None:
    process = subprocess.Popen(f'ngrok http {env.port} --log "stdout"',
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
            LOGGER.warning("Interrupted manually")
            break
    process.kill()
    LOGGER.warning("Connection closed")
