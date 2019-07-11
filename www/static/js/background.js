document.addEventListener('DOMContentLoaded', function () {
	var POINT = 35;

	var canvas = document.createElement('canvas');
	document.body.appendChild(canvas);
	canvas.width = window.innerWidth;
	canvas.height = window.innerHeight;

	window.onresize = function () {
		canvas.width = window.innerWidth;
		canvas.height = window.innerHeight;
	};

	var context = canvas.getContext("2d");
	var circleArr = [];

	//线条：开始xy坐标，结束xy坐标，线条透明度
	function Line(x, y, _x, _y, o) {
		this.beginX = x;
		this.beginY = y;
		this.closeX = _x;
		this.closeY = _y;
		this.o = o;
	}

	//点：圆心xy坐标，半径，每帧移动xy的距离
	function Circle(x, y, r, moveX, moveY) {
		this.x = x;
		this.y = y;
		this.r = r;
		this.moveX = moveX;
		this.moveY = moveY;
	}

	//生成max和min之间的随机数
	function num(max, _min) {
		var min = arguments[1] || 0;
		return Math.floor(Math.random() * (max - min + 1) + min);
	}

	// 绘制原点
	function drawCricle(cxt, x, y, r, moveX, moveY) {
		var circle = new Circle(x, y, r, moveX, moveY);
		cxt.beginPath();
		cxt.arc(circle.x, circle.y, circle.r, 0, 2 * Math.PI);
		cxt.closePath();
		cxt.fillStyle = "rgba(0,0,0,0.1)";
		cxt.fill();
		return circle;
	}

	//绘制线条
	function drawLine(cxt, x, y, _x, _y, o) {
		var line = new Line(x, y, _x, _y, o);
		cxt.beginPath();
		cxt.strokeStyle = "rgba(0,0,0," + o + ")";
		cxt.moveTo(line.beginX, line.beginY);
		cxt.lineTo(line.closeX, line.closeY);
		cxt.closePath();
		cxt.stroke();
	}

	//每帧绘制
	function draw() {
		context.clearRect(0, 0, canvas.width, canvas.height);
		for (var i = 0; i < POINT; i++) {
			drawCricle(context, circleArr[i].x, circleArr[i].y, circleArr[i].r);
		}
		for (var i = 0; i < POINT; i++) {
			for (var j = 0; j < POINT; j++) {
				if (i + j < POINT) {
					var A = Math.abs(circleArr[i + j].x - circleArr[i].x),
						B = Math.abs(circleArr[i + j].y - circleArr[i].y);
					var lineLength = Math.sqrt(A * A + B * B);
					var C = (1 / lineLength) * 7 - 0.009;
					var lineOpacity = C > 0.03 ? 0.03 : C;
					if (lineOpacity > 0) {
						drawLine(
							context,
							circleArr[i].x,
							circleArr[i].y,
							circleArr[i + j].x,
							circleArr[i + j].y,
							lineOpacity
						);
					}
				}
			}
		}
	}

	//初始化生成原点
	function init() {
		circleArr = [];
		for (var i = 0; i < POINT; i++) {
			circleArr.push(
				drawCricle(
					context,
					num(window.innerWidth),
					num(window.innerHeight),
					num(15, 2),
					num(10, -10) / 40,
					num(10, -10) / 40
				)
			);
		}
		draw();
	}

	//调用执行
	window.onload = function () {
		init();
		setInterval(function () {
			for (var i = 0; i < POINT; i++) {
				var cir = circleArr[i];
				cir.x += cir.moveX;
				cir.y += cir.moveY;
				if (cir.x > innerWidth) cir.x = 0;
				else if (cir.x < 0) cir.x = innerWidth;
				if (cir.y > window.innerHeight) cir.y = 0;
				else if (cir.y < 0) cir.y = window.innerHeight;
			}
			draw();
		}, 10);
	};

	canvas.style.cssText = "position:fixed;top:0;left:0;z-index:-1; opacity:1";
});