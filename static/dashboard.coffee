
MAX_EVENTS = 50

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
                    if item.device in data.pd_to_ld
                        item.member = true
                        item.volume = data.pd_to_ld[item.device].ld
                    else
                        item.member = false
                    @devices.push item
                )

            $.get '/api/events/', {limit: MAX_EVENTS}, (data, status) =>
                @last_event = 0
                $.each(data.events, (idx, item) =>
                    @last_event = Math.max @last_event, item.id
                    @events.unshift item
                )
                delay 4000, @pollEvents

        @pollEvents = =>
            $.get('/api/events/', {since: @last_event}, (data, status) =>
                $.each data.events, (idx, item) =>
                    @last_event = Math.max @last_event, item.id
                    @events.unshift item 
                    if @events().length > MAX_EVENTS
                        @events.pop
                delay 4000, @pollEvents
            )

vm = new ViewModel()
ko.applyBindings vm

$ ->
    vm.loadData()

