#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;

void main(){
  vec2 st = gl_FragCoord.xy/u_resolution.xy;

  gl_FragColor = vec4(vec3(st.y, abs(cos(0.5 * u_time)), abs(sin(u_time))),1.0);
}
