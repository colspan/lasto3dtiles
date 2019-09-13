require('cesium/Widgets/widgets.css');
require('./css/main.css');

var Cesium = require('cesium/Cesium');

function getHashVars() {
    var vars = {};
    var hashes = window.location.href.slice(window.location.href.indexOf('#') + 1).split('&');
    hashes.forEach(hash => {
      var entry = hash.split('=');
      vars[entry[0]] = entry[1];
    });
    return vars;
  }

var viewer = new Cesium.Viewer('cesiumContainer', {
    imageryProvider: null,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false
  });

var globe = viewer.scene.globe;
globe.imageryLayers.removeAll();
globe.baseColor = Cesium.Color.fromCssColorString('#000000');

var gsiOrt = globe.imageryLayers.addImageryProvider(new Cesium.createOpenStreetMapImageryProvider({
  url: 'https://cyberjapandata.gsi.go.jp/xyz/ort/',
  fileExtension: 'jpg',
  maximumLevel: 18,
  credit: new Cesium.Credit('地理院タイル', '', 'https://maps.gsi.go.jp/development/ichiran.html')
}));
gsiOrt.alpha = 0.5;
gsiOrt.brightness = 0.5;

var hashVars = getHashVars();
var targetDir = 'default';
if (hashVars.name) {
  targetDir = hashVars.name;
}
var tileset = viewer.scene.primitives.add(new Cesium.Cesium3DTileset({
    url : './var/3dtiles/' + targetDir + '/tileset.json'
}));

var scene = viewer.scene;
scene.debugShowFramesPerSecond = true;

var entity = viewer.entities.add({
    label : {
        show : false,
        showBackground : true,
        font : '14px monospace',
        horizontalOrigin : Cesium.HorizontalOrigin.LEFT,
        verticalOrigin : Cesium.VerticalOrigin.TOP,
        pixelOffset : new Cesium.Cartesian2(15, 0)
    }
});
handler = new Cesium.ScreenSpaceEventHandler(scene.canvas);
handler.setInputAction(function(movement) {
    var cartesian = viewer.camera.pickEllipsoid(movement.endPosition, scene.globe.ellipsoid);
    if (cartesian) {
        var cartographic = Cesium.Cartographic.fromCartesian(cartesian);
        var longitudeString = Cesium.Math.toDegrees(cartographic.longitude).toFixed(2);
        var latitudeString = Cesium.Math.toDegrees(cartographic.latitude).toFixed(2);

        entity.position = cartesian;
        entity.label.show = true;
        entity.label.text =
            'Lon: ' + ('   ' + longitudeString).slice(-7) + '\u00B0' +
            '\nLat: ' + ('   ' + latitudeString).slice(-7) + '\u00B0';
    } else {
        entity.label.show = false;
    }
}, Cesium.ScreenSpaceEventType.MOUSE_MOVE);


var emitterModelMatrixScratch = new Cesium.Matrix4();
var center = Cesium.Cartesian3.fromDegrees(137.77814451006, 34.823883);
// var center = Cesium.Cartesian3.fromDegrees(0.8987233516605286, -0.0005682966577418737);
// var emitterInitialLocation = new Cesium.Cartesian3(0.0, 0.0, 1000.0);
// viewer.camera.lookAt(center, emitterInitialLocation);

tileset.style = new Cesium.Cesium3DTileStyle({
    pointSize : '3.0'
});

tileset.readyPromise.then(function(tileset) {
    console.log(tileset)
    viewer.camera.viewBoundingSphere(tileset.boundingSphere, new Cesium.HeadingPitchRange(0, -0.5, 0));
    viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
});
