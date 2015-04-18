
MAX_EVENTS = 50
EVENT_POLLING_PERIOD = 4000

delay = (ms, func) -> setTimeout func, ms

numberWithCommas = (x) -> x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")

sectorsToMB = (x) -> Math.floor x * 512 / (1000 * 1000)

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
        delay EVENT_POLLING_PERIOD, @pollEvents

    @pollEvents = =>
      $.get('/api/events/', {since: @last_event}, (data, status) =>
        $.each(data.events, (idx, item) =>
          @last_event = Math.max @last_event, item.id
          @events.unshift item
          if @events().length > MAX_EVENTS
            @events.pop
        )
      ).always(=>
        delay EVENT_POLLING_PERIOD, @pollEvents
      )

vm = new ViewModel()
ko.applyBindings vm

$ ->
  vm.loadData()

