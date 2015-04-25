define ['knockout', 'moment', 'app/eventbus', 'text!./status_page.html', 'ko.plus'], (ko, moment, eventbus, pageHtml) ->

  MAX_EVENTS = 50
  EVENT_POLLING_PERIOD = 4000

  delay = (ms, func) -> setTimeout func, ms

  class StatusPageViewModel
    constructor: () ->
      @last_event = 0
      @events = ko.observableArray()
      @adapter = ko.observable()
      @volumes = ko.observableArray()
      @devices = ko.observableArray()

      @moment = (x) -> moment(x)
      @numberWithCommas = (x) -> x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",")
      @sectorsToMB = (x) -> Math.floor x * 512 / (1000 * 1000)

      @loadMain = ko.command(=>
        return $.get('/api/adapter/', {})
      ).done((data) =>
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
      ).fail((error) =>
        console.log('failure while loading adapter data')
      )

      @loadEvents = ko.command(=>
        return $.get('/api/events/', {limit: MAX_EVENTS})
      ).done((data) =>
        @last_event = 0
        $.each data.events.reverse(), (idx, item) =>
          @last_event = Math.max @last_event, item.id
          @events.push item
      ).fail((error) =>
        console.log('failure while loading events')
      )

      @pollEvents = =>
        $.get('/api/events/', {since: @last_event}, (data, status) =>
          $.each(data.events, (idx, item) =>
            @last_event = Math.max @last_event, item.id
            @events.unshift item
            if @events().length > MAX_EVENTS
              @events.pop
          )
        )

      @loadMain()
      @loadEvents()
      eventbus.receivers.push =>
        @pollEvents()

  return {
    viewModel: StatusPageViewModel,
    template: pageHtml
  }

