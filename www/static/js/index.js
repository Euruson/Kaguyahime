import Vue from 'vue';
import UIkit from 'uikit';
import Icons from 'uikit/dist/js/uikit-icons';
import CryptoJS from 'crypto-js'
import jquery from 'jquery'
import SimpleMDE from 'simplemde'
import Pagination from './component/Pagination.vue'

window.Vue = Vue;
Vue.component('pagination',Pagination);
window.CryptoJS = CryptoJS;
//window.SimpleMDE = SimpleMDE;
UIkit.use(Icons);