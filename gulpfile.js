// Node modules
var fs = require('fs'),
    vm = require('vm'),
    merge = require('deeply'),
    chalk = require('chalk'),
    es = require('event-stream');

// Gulp and plugins
var gulp = require('gulp'),
    rjs = require('gulp-requirejs-bundler'),
    concat = require('gulp-concat'),
    clean = require('gulp-clean'),
    replace = require('gulp-replace'),
    uglify = require('gulp-uglify'),
    htmlreplace = require('gulp-html-replace'),
    coffee = require('gulp-coffee');

var base_bower = 'bower_components';
var base_static = 'static';

// Config
var requireJsRuntimeConfig = vm.runInNewContext(fs.readFileSync('static/app/require.config.js') + '; require;');
    requireJsOptimizerConfig = merge(requireJsRuntimeConfig, {
        out: 'scripts.js',
        baseUrl: './static',
        name: 'app/startup',
        paths: {
            requireLib: 'bower_components/requirejs/require'
        },
        include: [
            'requireLib',
            'app/status_page',
            'text!app/status_page.html',
        ],
        insertRequire: ['app/startup'],
        bundles: {
            // If you want parts of the site to load on demand, remove them from the 'include' list
            // above, and group them into bundles here.
            // 'bundle-name': [ 'some/module', 'another/module' ],
            // 'another-bundle-name': [ 'yet-another-module' ]
        }
    });

// Compile all .coffee files, producing .js and source map files alongside them
gulp.task('cs', function () {
    return gulp.src(['**/*.coffee'])
        .pipe(coffee({bare: true}))
        .pipe(gulp.dest('./'));
});

// Discovers all AMD dependencies, concatenates together all required .js files, minifies them
gulp.task('js', ['cs'], function () {
    return rjs(requireJsOptimizerConfig)
        .pipe(uglify({ preserveComments: 'some' }))
        .pipe(gulp.dest('./dist/'));
});

// Concatenates CSS files, rewrites relative paths to Bootstrap fonts, copies Bootstrap fonts
gulp.task('css', function () {
    var bootswatchCss = gulp.src('static/bower_components/bootswatch/superhero/bootstrap.min.css'),
        fontawesomeCss = gulp.src('static/bower_components/fontawesome/css/font-awesome.min.css')
            .pipe(replace(/url\((')?\.\.\/fonts\//g, 'url($1fonts/')),
            //.pipe(replace(/url\((')?\.\.\/fonts\//g, 'url($1fonts/')),
        appCss = gulp.src('static/css/*.css'),
        combinedCss = es.concat(bootswatchCss, fontawesomeCss, appCss).pipe(concat('css.css')),
        fontFiles = gulp.src('./static/bower_components/fontawesome/fonts/*', { base: './static/bower_components/fontawesome/' });
    return es.concat(combinedCss, fontFiles)
        .pipe(gulp.dest('./dist/'));
});

// Copies index.html, replacing <script> and <link> tags to reference production URLs
gulp.task('html', function () {
    return gulp.src('./static/index.html')
        .pipe(htmlreplace({
            'css': 'css.css',
            'js': 'scripts.js'
        }))
        .pipe(gulp.dest('./dist/'));
});

// Removes all files from ./dist/, and the .js/.js.map files compiled from .ts
gulp.task('clean', function () {
    var distContents = gulp.src('./dist/**/*', {read: false}),
        generatedJs = gulp.src(['static/**/*.js', 'static/**/*.js.map'], {read: false})
            .pipe(es.mapSync(function (data) {
                // Include only the .js/.js.map files that correspond to a .ts file
                return fs.existsSync(data.path.replace(/\.js(\.map)?$/, '.coffee')) ? data : undefined;
            }));
    return es.merge(distContents, generatedJs).pipe(clean());
});

gulp.task('default', ['html', 'js', 'css'], function (callback) {
    callback();
    console.log('\nPlaced optimized files in ' + chalk.magenta('dist/\n'));
});

