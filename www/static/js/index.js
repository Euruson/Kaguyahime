import Vue from 'vue';
import UIkit from 'uikit';
import Icons from 'uikit/dist/js/uikit-icons';
import CryptoJS from 'crypto-js'
import jquery from 'jquery'
import SimpleMDE from 'simplemde'
import VueSimplemde from 'vue-simplemde'
import Pagination from './component/Pagination.vue'
import VoerroTagsInput from '@voerro/vue-tagsinput';

import 'simplemde/dist/simplemde.min.css'
import'uikit/dist/css/uikit.min.css'
import '@voerro/vue-tagsinput/dist/style.css'

Vue.component('pagination',Pagination);
Vue.component('tags-input',VoerroTagsInput);
Vue.component('vue-simplemde', VueSimplemde);

window.Vue = Vue;
window.CryptoJS = CryptoJS;
window.SimpleMDE = SimpleMDE;
UIkit.use(Icons);