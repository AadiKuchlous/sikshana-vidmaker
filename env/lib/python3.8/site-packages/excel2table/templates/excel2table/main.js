define(["require", "exports"], function (require, exports) {
    "use strict";
    Object.defineProperty(exports, "__esModule", { value: true });
    var version = '2.3.0';
    function load_ipython_extension() {
        console.log("excel2table " + version + " (echarts 3.6.2) has been loaded");
    }
    exports.load_ipython_extension = load_ipython_extension;
});
