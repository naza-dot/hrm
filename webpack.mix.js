const mix = require('laravel-mix');

mix.sass('static/src/scss/main.scss', 'css/style.min.css')
   .options({ processCssUrls: false })
   .setPublicPath('static/build')
   .disableNotifications();

if (mix.inProduction()) {
    mix.version();
}
