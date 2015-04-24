define(['sockjs'], (SockJS) ->

  class EventBus
    constructor: () ->
      @attempts = 0
      @attempt_delay = 500
      @socket = null
      @receivers = []

      @connect = ->
        console.log('Connecting eventbus')
        @socket = new SockJS('/chan')
        if @attempt_delay < 15000
          @attempt_delay *= 2
        @attempts += 1
        @socket.onopen = ->
          @attempts = 0
          @attempt_delay = 500
        @socket.onclose = ->
          @socket = null
          delay @attempt_delay, @connect
        @socket.onmessage = (e) ->
          for item, idx in @receivers
            item?(e)

  eventbus = new EventBus()
  eventbus.connect()
  return eventbus

)
