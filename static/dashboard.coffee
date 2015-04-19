requirejs.config {
  baseUrl: 'static',
  paths: {
    sockjs: 'sockjs/sockjs.min',
    moment: 'moment/min/moment.min',
    jquery: 'jquery/dist/jquery.min',
    knockout: 'knockout/dist/knockout',
    bootstrap: 'bootstrap/dist/js/bootstrap.min'
  }
}

require ['jquery', 'bootstrap', 'knockout', 'moment', 'sockjs'],
         (jquery, bootstrap, ko, moment, SockJS) ->

  MAX_EVENTS = 50
  EVENT_POLLING_PERIOD = 4000

  delay = (ms, func) -> setTimeout func, ms

  class ViewModel
    constructor: () ->
      @last_event = 0
      @events = ko.observableArray()
      @adapter = ko.observable()
      @volumes = ko.observableArray()
      @devices = ko.observableArray()

      @loadData = =>
        $.get '/api/adapter/', {}, (data, status) =>
          @adapter(data.ad)
          ko.utils.arrayPushAll @volumes, data.ld
          @devices.removeAll()
          $.each(data.pd, (idx, item) =>
            if item.device of data.pd_to_ld
              item.member = true
              item.volume = data.pd_to_ld[item.device].ld
            else
              item.member = false
            @devices.push item
          )

        $.get '/api/events/', {limit: MAX_EVENTS}, (data, status) =>
          @last_event = 0
          $.each data.events.reverse(), (idx, item) =>
            @last_event = Math.max @last_event, item.id
            @events.push item

      @pollEvents = =>
        $.get('/api/events/', {since: @last_event}, (data, status) =>
          $.each(data.events, (idx, item) =>
            @last_event = Math.max @last_event, item.id
            @events.unshift item
            if @events().length > MAX_EVENTS
              @events.pop
          )
        )

      @numberWithCommas = (x) -> x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")

      @sectorsToMB = (x) -> Math.floor x * 512 / (1000 * 1000)

  vm = new ViewModel()
  ko.applyBindings vm

  attempts = 0
  attempt_delay = 500
  socket = null

  connectEventBus = ->
    socket = new SockJS('/chan')
    if attempt_delay < 15000
      attempt_delay *= 2
    attempts += 1
    socket.onopen = ->
      attempts = 0
      attempt_delay = 500
    socket.onclose = ->
      socket = null
      delay attempt_delay, connectEventBus
    socket.onmessage = (e) ->
      vm.pollEvents()

  $ ->
    vm.loadData()
    connectEventBus()

