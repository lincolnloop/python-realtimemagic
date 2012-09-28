from realtimemagic import RealTimeMagic


def on_open(self, conn_info):
    self.subscribe({'channel': 'echo'})


def echo(conn, message):
    #conn.master.slow_stuff(5)
    conn.master.publish('echo', message)

if __name__ == '__main__':
    rtm = RealTimeMagic(local=False)
    rtm.openings.append(on_open)
    rtm.receivers.append(echo)
    #rtm.monitors.append(log_changes)
    #rtm.authenticators['default'].append(BotBotAuthenticator())
    rtm.start()
