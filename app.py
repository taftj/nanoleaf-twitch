import requests
import configparser
import time

CONFIG_PATH = 'C:/Users/Justin/nano_twitch_config'
config = configparser.ConfigParser()

def flash_panels(alt_mode=False):
    r = requests.get(config['Nanoleaf']['nano_host'] + '/state')
    if r.json()['on']['value'] == True:
        #Grab current mode, notify that a caster has gone live, return to original mode
        current_mode = requests.get(config['Nanoleaf']['nano_host'] + '/effects/select').json()
        if alt_mode:
            requests.put(config['Nanoleaf']['nano_host'] + '/effects/select', json={'select': 'Synthwave'})
        else:
            requests.put(config['Nanoleaf']['nano_host'] + '/effects/select', json={'select': 'Lightning'})
        time.sleep(3)
        requests.put(config['Nanoleaf']['nano_host'] + '/effects/select', json={'select': current_mode})


def get_twitch_token():
    r = requests.post('https://id.twitch.tv/oauth2/token?client_id=%s&client_secret=%s&grant_type=client_credentials' % \
                        (config['Twitch']['client_id'], config['Twitch']['client_secret']))
    return r.json()['access_token']

def main():
    def update_broadcaster_status(caster_list):
        currently_live = []
        for caster in caster_list:
            currently_live.append(caster['user_id'])
            if broadcaster_status[caster['user_id']] == 'Offline':
                broadcaster_status[caster['user_id']] = 'Live'
                if broadcaster_status[caster['user_id']] == config['Twitch']['manvsgame']:
                    flash_panels(alt_mode=True)
                else:
                    flash_panels()
        #Set the status of any casters who have gone offline
        for key in broadcaster_status.keys():
            if broadcaster_status[key] == 'Live' and (key not in currently_live):
                broadcaster_status[key] = 'Offline'

    config.read(CONFIG_PATH)
    id_list_as_string = ''
    broadcaster_status = {}
    #Grab a new authorization token
    token = get_twitch_token()

    #Start by grabbing casters I follow
    r = requests.get('https://api.twitch.tv/helix/users/follows?first=100&from_id=%s' % config['Twitch']['my_id'], \
                     headers={'Authorization': 'Bearer %s' % token})

    for n in r.json()['data']:
        broadcaster_status[n['to_id']] = 'Live' #Default all casters as Live
        id_list_as_string = id_list_as_string + 'user_id=' + n['to_id'] + '&'

    id_list_as_string = id_list_as_string[:-1] #Trim off last ampersand

    while True:
        try:            
            #Get the status of casters I follow
            r = requests.get('https://api.twitch.tv/helix/streams?%s' % id_list_as_string, \
                             headers={'Authorization': 'Bearer %s' % token})

            update_broadcaster_status(r.json()['data'])
            print 'Waiting for twitch casters to go live...'
            time.sleep(1)
        except Exception as e:
            print 'Whoops, we got an error! Lets refresh our token just in case\n %s' % e
            print r.json()
            token = get_twitch_token()
            continue

if __name__ == '__main__':
    main()