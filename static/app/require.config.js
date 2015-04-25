var require = {
  baseUrl: '.',
  paths: {
    text: 'bower_components/requirejs-text/text',
    sockjs: 'bower_components/sockjs/sockjs.min',
    moment: 'bower_components/moment/min/moment.min',
    jquery: 'bower_components/jquery/dist/jquery.min',
    knockout: 'bower_components/knockout/dist/knockout',
    'ko.plus': 'bower_components/ko.plus/dist/ko.plus.min',
    bootstrap: 'bower_components/bootstrap/dist/js/bootstrap.min',
  },
  shim: {
    bootstrap: {
      deps: ['jquery']
    }
  }
};
