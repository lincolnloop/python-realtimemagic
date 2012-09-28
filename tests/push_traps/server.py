from realtimemagic import RealTimeMagic


def change_the_published_messages(conn, channel, message):
    conn.master.publish(channel, '[ %s ]' % message,
        async=False)  # No need to spawn a new thread
    return False  # Don't send the message

if __name__ == '__main__':
    rtm = RealTimeMagic()
    rtm.push_traps.append(change_the_published_messages)
    rtm.start()
