const { defineConfig } = require('@vue/cli-service');
const webpack = require('webpack');

module.exports = defineConfig({
  transpileDependencies: [],
  outputDir: 'static',
  publicPath: '/', 
  assetsDir: '', 
  
  devServer: {
    proxy: {
      '/': {
        target: 'http://localhost:5001',
        ws: false,
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