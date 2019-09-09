Cesium.Ion.defaultAccessToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiIxZjJkZTcxZi1lNWU0LTRhOTgtYWRmNS00NGJmMTE0ZTg0ZTUiLCJpZCI6NDgxOCwic2NvcGVzIjpbImFzciIsImdjIl0sImlhdCI6MTU0MTY5MDk1Mn0.Itk3_QIKsYzYNkqDSRBptj2sgvOv7o1_1fxYpYxdptA';

function getHashVars() {
    var vars = {};
    var hashes = window.location.href.slice(window.location.href.indexOf('#') + 1).split('&');
    hashes.forEach(hash => {
      var entry = hash.split('=');
      vars[entry[0]] = entry[1];
    });
    return vars;
  }

var viewer = new Cesium.Viewer('cesiumContainer');

var hashVars = getHashVars();
var targetDir = 'default';
if (hashVars.name) {
  targetDir = hashVars.name;
}
var tileset = viewer.scene.primitives.add(new Cesium.Cesium3DTileset({
    url : './var/3dtiles/' + targetDir
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
    pointSize : '4.0'
});

tileset.readyPromise.then(function(tileset) {
    console.log(tileset)
    viewer.camera.viewBoundingSphere(tileset.boundingSphere, new Cesium.HeadingPitchRange(0, -0.5, 0));
    viewer.camera.lookAtTransform(Cesium.Matrix4.IDENTITY);
});

console.log(tileset);
