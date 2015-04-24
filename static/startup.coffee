define(['jquery', 'knockout', 'moment', 'sockjs', 'bootstrap'],\
        ($, ko, moment, SockJS) ->

  ko.components.register('status_page', {require: 'static/status_page'})
  ko.applyBindings({})

)
