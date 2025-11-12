/**
 * @license Copyright (c) 2003-2019, CKSource - Frederico Knabben. All rights reserved.
 * For licensing, see https://ckeditor.com/legal/ckeditor-oss-license
 */


CKEDITOR.on('instanceReady', function (ev) {
   ev.editor.dataProcessor.htmlFilter.addRules(
    {
       elements:
        {
          $: function (element) {
            // check for the tag name
            if (element.name == 'img') {

                element.attributes.class = "img-fluid" // Put your class name here
            }

            // return element with class attribute
            return element;
         }
       }
   });
 });