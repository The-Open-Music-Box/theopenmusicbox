const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');

module.exports = defineConfig({
  transpileDependencies: [],
  outputDir: 'static',
  publicPath: '/', 
  assetsDir: '', 
  
  devServer: {
    proxy: {
      '^/api': {
        target: 'http://10.0.0.153:5003',
        changeOrigin: true,
        ws: false,
        logLevel: 'debug',  // Pour plus de détails dans les logs
        onError: (err, req, res) => {
          console.log('Proxy Error:', err);
      },
      onProxyReq: (proxyReq, req, res) => {
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