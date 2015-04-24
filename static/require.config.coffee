require = {
  baseUrl: 'static',
  paths: {
    text: 'requirejs-text/text'
    sockjs: 'sockjs/sockjs.min'
    moment: 'moment/min/moment.min'
    jquery: 'jquery/dist/jquery.min'
    hasher: 'hasher/disk/js/hasher.min'
    signals: 'js-signals/dist/signals.min'
    knockout: 'knockout/dist/knockout'
    bootstrap: 'bootstrap/dist/js/bootstrap.min'
    crossroads: 'crossroads/dist/crossroads.min'
  },
  shim: {
    bootstrap: {deps: ['jquery']}
  }
}

