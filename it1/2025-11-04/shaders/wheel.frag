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
  float a = atan(pos.y,pos.x);

  float f = 3. * sin(12.*a + u_time);

  color = mix(vec3(fract(r), mod(0.5, a), 0.), color, f);

  gl_FragColor = vec4(color,1.0);
}
