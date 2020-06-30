const {src, dest, parallel, series} = require('gulp');
const cleanCSS = require('gulp-clean-css')
const babel = require('gulp-babel')
const uglify = require('gulp-uglify')

function cssNNR(cb) {
    return src('css/nnr/*.css')
      .pipe(cleanCSS({compatibility: 'ie8'}))
      .pipe(dest('../nnr/static/css/'))
  }

function cssComments(cb) {
    return src('css/comments/*.css')
      .pipe(cleanCSS({compatibility: 'ie8'}))
      .pipe(dest('../comments/static/css/'))
  }  

  function javascriptNNR(cb) {
    return src('js/nnr/*.js')
      .pipe(babel({
        presets: ["@babel/env"]
      }))
      .pipe(uglify())
      .pipe(dest('../nnr/static/js/'))
  }

  function javascriptComments(cb) {
    return src('js/comments/*.js')
      .pipe(babel({
        presets: ["@babel/env"]
      }))
      .pipe(uglify())
      .pipe(dest('../comments/static/js/'))
  }
  
  exports.default = parallel(series(javascriptNNR, javascriptComments), series(cssNNR, cssComments));

  