define ['sockjs'], (SockJS) ->

  delay = (ms, func) -> setTimeout func, ms

  class EventBus
    constructor: () ->
      @attempts = 0
      @attempt_delay = 500
      @socket = null
      @receivers = []

      @connect = =>
        console.log('eventbus: Connecting, attempt ' + @attempts)
        @socket = new SockJS('/chan')
        if @attempt_delay < 15000
          @attempt_delay *= 2
        @attempts += 1
        @socket.onopen = =>
          console.log('eventbus: Connected')
          @attempts = 0
          @attempt_delay = 500
        @socket.onclose = =>
          console.log('eventbus: Closed')
          @socket = null
          delay @attempt_delay, @connect
        @socket.onmessage = (e) =>
          msg = JSON.parse(e.data)
          if msg.ch == 'beat'
            console.log('eventbus: heartbeat \"' + msg.data + '\"')
          else if msg.ch == 'hello'
            console.log('eventbus says hello ' + msg.data)
          else
            console.log('eventbus: Message Received', e)
            for item, idx in @receivers
              item?(msg)

  eventbus = new EventBus()
  eventbus.connect()
  return eventbus

