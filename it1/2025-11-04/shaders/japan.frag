#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;

void main(){
  vec2 st = gl_FragCoord.xy/u_resolution.xy;

  vec3 color = vec3(1.);
  vec2 center = vec2(0.5);
  vec2 pos = center - st;

  float r = length(pos) * 2.0;
  float a = atan(st.x + st.y);

  float circle = 0.3 * abs(sin(1.5 * u_time)) + 0.3;
  color = mix(vec3(1.0, 0., 0.), color, smoothstep(circle, circle + circle * 0.01, r));

  gl_FragColor = vec4(color,1.0);
}
