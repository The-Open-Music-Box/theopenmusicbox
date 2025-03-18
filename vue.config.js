const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');

module.exports = defineConfig({
  transpileDependencies: [],
  outputDir: process.env.VUE_APP_OUTPUT_DIR,
  publicPath: process.env.VUE_APP_PUBLIC_PATH,
  assetsDir: process.env.VUE_APP_ASSETS_DIR,

  devServer: {
    proxy: {
      '^/api': {
        target: process.env.VUE_APP_API_URL,
        changeOrigin: true,
        ws: false,
        logLevel: 'debug',  // Pour plus de détails dans les logs
        onError: (err) => {
          console.log('Proxy Error:', err);
      },
      onProxyReq: (proxyReq, req) => {
        console.log('Proxying:', req.method, req.url, '→', proxyReq.path);
      }
    }
    },
  },

  configureWebpack: {
    plugins: [
      new webpack.DefinePlugin({
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(true),
      }),
    ],
  },
});