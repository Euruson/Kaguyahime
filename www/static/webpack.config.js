var path = require('path');
var glob = require('glob');
var webpack = require('webpack');
const MergeIntoSingleFilePlugin = require('webpack-merge-and-include-globally');
const VueLoaderPlugin = require('vue-loader/lib/plugin')




//定义了一些文件夹的路径
var ROOT_PATH = path.resolve(__dirname);
var APP_PATH = path.resolve(ROOT_PATH, 'js');
var BUILD_PATH = path.resolve(ROOT_PATH);


module.exports = {
	//项目的文件夹 可以直接用文件夹名称 默认会找index.js 也可以确定是哪个文件名字
	entry: path.resolve(ROOT_PATH, './js/index.js'),
	//输出的文件名 合并以后的js会命名为bundle.js
	output: {
		path: BUILD_PATH,
		filename: 'bundle.js'
	},
	devServer: {
		historyApiFallback: true,
		hot: true,
		inline: true,
		progress: true,
	},
	resolve: {
		alias: {
			'vue$': 'vue/dist/vue.esm.js'
		}
	},
	module: {
		rules: [
			{
                test: /\.(woff|ttf|eot|png|jpg|gif|svg)$/,
                loader: 'file-loader',
                options: {
                    name: './images/[name].[ext]'
                }
			},
			{
                test: /\.css$/,
                use: [
                    {
                        loader: 'style-loader'
                    },
                    {
                        loader: 'css-loader'
                    }
                ]
            },
			{
				test: /\.vue$/,
				loader: 'vue-loader'
			},
			{
				test: require.resolve('jquery'),
				use: [{
					loader: 'expose-loader',
					options: '$'
				}]
			}]
	},
	plugins:
		[
			new VueLoaderPlugin(),
			new webpack.ProvidePlugin({
				$: 'jquery',
				jQuery: 'jquery'
			}),
			new MergeIntoSingleFilePlugin({
				files: {
					"vendor.js": [
						'js/awesome.js',
						'js/background.js'
					],
				}
			})
		],
	watch: true,
}; 