"use strict";function asyncGeneratorStep(e,t,n,r,a,o,i){try{var c=e[o](i),u=c.value}catch(e){return void n(e)}c.done?t(u):Promise.resolve(u).then(r,a)}function _asyncToGenerator(c){return function(){var e=this,i=arguments;return new Promise(function(t,n){var r=c.apply(e,i);function a(e){asyncGeneratorStep(r,t,n,a,o,"next",e)}function o(e){asyncGeneratorStep(r,t,n,a,o,"throw",e)}a(void 0)})}}function _createForOfIteratorHelper(e,t){var n;if("undefined"==typeof Symbol||null==e[Symbol.iterator]){if(Array.isArray(e)||(n=_unsupportedIterableToArray(e))||t&&e&&"number"==typeof e.length){n&&(e=n);var r=0,a=function(){};return{s:a,n:function(){return r>=e.length?{done:!0}:{done:!1,value:e[r++]}},e:function(e){throw e},f:a}}throw new TypeError("Invalid attempt to iterate non-iterable instance.\nIn order to be iterable, non-array objects must have a [Symbol.iterator]() method.")}var o,i=!0,c=!1;return{s:function(){n=e[Symbol.iterator]()},n:function(){var e=n.next();return i=e.done,e},e:function(e){c=!0,o=e},f:function(){try{i||null==n.return||n.return()}finally{if(c)throw o}}}}function _unsupportedIterableToArray(e,t){if(e){if("string"==typeof e)return _arrayLikeToArray(e,t);var n=Object.prototype.toString.call(e).slice(8,-1);return"Object"===n&&e.constructor&&(n=e.constructor.name),"Map"===n||"Set"===n?Array.from(e):"Arguments"===n||/^(?:Ui|I)nt(?:8|16|32)(?:Clamped)?Array$/.test(n)?_arrayLikeToArray(e,t):void 0}}function _arrayLikeToArray(e,t){(null==t||t>e.length)&&(t=e.length);for(var n=0,r=new Array(t);n<t;n++)r[n]=e[n];return r}var _step,_iterator=_createForOfIteratorHelper(document.getElementsByClassName("untag-form"));try{for(_iterator.s();!(_step=_iterator.n()).done;)untagForm=_step.value,untagForm.addEventListener("submit",function(e){e.preventDefault(),untag(this)})}catch(e){_iterator.e(e)}finally{_iterator.f()}function untag(e){return _untag.apply(this,arguments)}function _untag(){return(_untag=_asyncToGenerator(regeneratorRuntime.mark(function e(r){var t;return regeneratorRuntime.wrap(function(e){for(;;)switch(e.prev=e.next){case 0:t={recipe:parseInt(r.recipe.value),tag_slug:r.tag_slug.value},fetch(r.action,{method:"post",headers:{"Content-Type":"application/json","X-CSRFToken":r.csrfmiddlewaretoken.value,Accept:"application/json","X-Requested-With":"XMLHttpRequest"},body:JSON.stringify(t)}).then(function(e){return e.json()}).then(function(e){var t,n;e.error?(t=createAlert(e.error,["alert-danger"]),$("#untag_".concat(r.tag_slug.value)).modal("hide"),document.getElementById("tag-container").before(t)):(n=createAlert(e.message,["alert-success"]),$("#untag_".concat(r.tag_slug.value)).modal("hide"),document.getElementById("tag-container").before(n),document.getElementById("untag-container_".concat(r.tag_slug.value)).remove())});case 2:case"end":return e.stop()}},e)}))).apply(this,arguments)}function get_all_tags(){return _get_all_tags.apply(this,arguments)}function _get_all_tags(){return(_get_all_tags=_asyncToGenerator(regeneratorRuntime.mark(function e(){return regeneratorRuntime.wrap(function(e){for(;;)switch(e.prev=e.next){case 0:fetch("/tags/all/",{method:"get",headers:{"Content-Type":"application/json",Accept:"application/json","X-Requested-With":"XMLHttpRequest"}}).then(function(e){return e.json()}).then(function(e){var t;e.error?(t=createAlert(e.error,["alert-danger"]),document.getElementById("id_tags").before(t)):(e.tag_list,autocomplete(document.getElementById("id_tags"),e.tag_list))});case 1:case"end":return e.stop()}},e)}))).apply(this,arguments)}function search_for_autocomplete(t,e){return e.filter(function(e){return-1<e.toLowerCase().search(t.toLowerCase())}).sort(function(e){return e.toLowerCase().search(t.toLowerCase())})}function autocomplete(l,n){var r;function a(e){e&&(function(e){for(var t=0;t<e.length;t++)e[t].classList.remove("autocomplete-active")}(e),r>=e.length&&(r=0),r<0&&(r=e.length-1),e[r].classList.add("autocomplete-active"))}function s(e){for(var t=document.getElementsByClassName("autocomplete-items"),n=0;n<t.length;n++)e!=t[n]&&e!=l&&t[n].parentNode.removeChild(t[n])}l.addEventListener("input",function(e){var i,c;if(lastComma=this.value.lastIndexOf(","),c=-1<lastComma?this.value.slice(lastComma+1).trim():this.value,s(),!c)return!1;r=-1;var u,t=search_for_autocomplete(c,n);(u=document.createElement("DIV")).setAttribute("id",this.id+"autocomplete-list"),u.setAttribute("class","autocomplete-items"),this.parentNode.appendChild(u),t.map(function(e){i=document.createElement("div");var t,n=new RegExp(c,"gi"),r=e.match(n,c),a=e,o=_createForOfIteratorHelper(r);try{for(o.s();!(t=o.n()).done;)occ=t.value,a=a.replace(occ,"<strong>".concat(occ,"</strong>"))}catch(e){o.e(e)}finally{o.f()}i.innerHTML=a,i.innerHTML+="<input type='hidden' value='".concat(e,"'>"),i.addEventListener("click",function(e){selected=this.getElementsByTagName("input")[0].value,lastComma=l.value.lastIndexOf(","),-1===lastComma?l.value=selected:l.value=l.value.slice(0,lastComma)+", ".concat(selected),s()}),u.appendChild(i)}),x=document.getElementById(this.id+"autocomplete-list"),x&&(ac_list=x.getElementsByTagName("div"),r=0,a(ac_list))}),l.addEventListener("keydown",function(e){var t=(t=document.getElementById(this.id+"autocomplete-list"))&&t.getElementsByTagName("div");40===e.keyCode?(r++,a(t)):38===e.keyCode?(r--,a(t)):13===e.keyCode||9===e.keyCode?(e.preventDefault(),-1<r&&t&&t[r].click()):188===e.keyCode&&s()}),document.addEventListener("click",function(e){s(e.target)})}get_all_tags();