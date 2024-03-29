////////////////////////////////
// Setup
////////////////////////////////

// Gulp and package
const { src, dest, parallel, series, watch } = require("gulp");
const pjson = require("./package.json");

// Plugins
const autoprefixer = require("autoprefixer");
const browserSync = require("browser-sync").create();

const concat = require("gulp-concat");

const cssnano = require("cssnano");
const pixrem = require("pixrem");
const plumber = require("gulp-plumber");
const postcss = require("gulp-postcss");
const reload = browserSync.reload;
const rename = require("gulp-rename");
const sass = require("gulp-sass")(require("sass"));
const spawn = require("child_process").spawn;
const uglify = require("gulp-uglify-es").default;

// Relative paths function
function pathsConfig(appName) {
  this.app = `./${pjson.name}`;
  const vendorsRoot = "node_modules";

  return {
    bootstrapSass: `${vendorsRoot}/bootstrap/scss`,
    vendorsJs: [
      `${vendorsRoot}/jquery/dist/jquery.slim.js`,
      `${vendorsRoot}/popper.js/dist/umd/popper.js`,
      `${vendorsRoot}/bootstrap/dist/js/bootstrap.js`,
    ],

    app: this.app,
    templates: `${this.app}/templates`,
    fonts: `${this.app}/static/fonts`,
    images: `${this.app}/static/images`,
    input: {
      sass: `${this.app}/static/input/sass`,
      js: `${this.app}/static/input/js`,
    },
    output: {
      css: `${this.app}/static/output/css`,
      js: `${this.app}/static/output/js`,
    },
  };
}

var paths = pathsConfig();

////////////////////////////////
// Tasks
////////////////////////////////

// Styles autoprefixing and minification
function projectStyles() {
  var processCss = [
    autoprefixer(), // adds vendor prefixes
    pixrem(), // add fallbacks for rem units
  ];

  var minifyCss = [
    cssnano({ preset: "default" }), // minify result
  ];

  return src(`${paths.input.sass}/project.scss`)
    .pipe(
      sass({
        includePaths: [paths.bootstrapSass, paths.sass],
      }).on("error", sass.logError)
    )
    .pipe(plumber()) // Checks for errors
    .pipe(postcss(processCss))
    .pipe(dest(paths.output.css))
    .pipe(rename({ suffix: ".min" }))
    .pipe(postcss(minifyCss)) // Minifies the result
    .pipe(dest(paths.output.css));
}

// Javascript minification
function scripts() {
  return src(`${paths.input.js}/*.js`)
    .pipe(plumber()) // Checks for errors
    .pipe(uglify()) // Minifies the js
    .pipe(rename({ suffix: ".min" }))
    .pipe(dest(paths.output.js));
}

// Vendor Javascript minification
function vendorScripts() {
  return src(paths.vendorsJs)
    .pipe(concat("vendors.js"))
    .pipe(dest(paths.output.js))
    .pipe(plumber()) // Checks for errors
    .pipe(uglify()) // Minifies the js
    .pipe(rename({ suffix: ".min" }))
    .pipe(dest(paths.output.js));
}

// Run django server
function runServer(cb) {
  var cmd = spawn("python", ["manage.py", "runserver"], { stdio: "inherit" });
  cmd.on("close", function (code) {
    console.log("runServer exited with code " + code);
    cb(code);
  });
}

// Browser sync server for live reload
function initBrowserSync() {
  browserSync.init(
    [`${paths.css}/*.css`, `${paths.js}/*.js`, `${paths.templates}/*.html`],
    {
      // https://www.browsersync.io/docs/options/#option-proxy
      proxy: "localhost:8000",
    }
  );
}

// Watch
function watchPaths() {
  watch(`${paths.input.sass}/project.scss`, projectStyles);
  watch(`${paths.templates}/**/*.html`).on("change", reload);
  watch([`${paths.input.js}/*.js`, `!${paths.js}/*.min.js`], scripts).on(
    "change",
    reload
  );
}

// Generate all assets
const generateAssets = parallel(projectStyles, scripts, vendorScripts);

// Set up dev environment
const dev = parallel(runServer, initBrowserSync, watchPaths);

exports.default = series(generateAssets, dev);
exports["generate-assets"] = generateAssets;
exports["dev"] = dev;
