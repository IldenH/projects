#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;

float rect(in vec2 st, in vec2 size) {
	// bottom-left
    vec2 bl = step(vec2(size),st);
    float pct = bl.x * bl.y;

    // top-right
    vec2 tr = step(vec2(size),1.0-st);
	pct *= tr.x * tr.y;

    return pct;
}

float rect_outline(in vec2 st, in vec2 size, in float border) {
	float rect_1 = rect(st, vec2(size));
    float rect_2 = rect(st, vec2(size + border));

    return rect_1 - rect_2;
}

void main(){
    vec2 st = gl_FragCoord.xy/u_resolution.xy;

    vec3 color = vec3(0.);

    vec3 bg = vec3(0.972, 0.949, 0.878);
    color = mix(color, bg, 1.0);

    float border = 0.05 * sin(u_time);

	float rect_5 = rect(vec2(-0.5,0.7) + st, vec2(0.2));
    color = mix(color, vec3(0.,0.37,0.61), rect_5);
	float rect_6 = rect(vec2(0.5,-0.5) + st, vec2(0.2));
    color = mix(color, vec3(0.69,0.13,0.13), rect_6);
    float rect_7 = rect(vec2(-0.7,-0.5) + st, vec2(0.2));
    color = mix(color, vec3(0.98,0.78,0.16), rect_7);

    float rect_1 = rect_outline(vec2(0.4,0.2) + st, vec2(0.3, 0.1), border);
    color = mix(color, vec3(0.), rect_1);
    float rect_2 = rect_outline(vec2(-0.255,0.1) + st, vec2(0., 0.2), border);
    color = mix(color, vec3(0.), rect_2);
    float rect_3 = rect_outline(vec2(-0.6,0.2) + st, vec2(0.3, 0.1), border);
    color = mix(color, vec3(0.), rect_3);
    float rect_4 = rect_outline(vec2(-0.3,0.2) + st, vec2(0.35, -0.6), border);
    color = mix(color, vec3(0.), rect_4);
    float rect_8 = rect_outline(vec2(0.,0.12) + st, vec2(-0.5, 0.), border);
    color = mix(color, vec3(0.), rect_8);
    float rect_9 = rect_outline(vec2(0.3,-1.25) + st, vec2(0.4, -0.6), border);
    color = mix(color, vec3(0.), rect_9);

    gl_FragColor = vec4(color,1.0);
}
