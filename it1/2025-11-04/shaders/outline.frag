#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform vec2 u_mouse;
uniform float u_time;

float plot(float d, float pct){
  return  smoothstep( pct-0.1, pct, d) -
          smoothstep( pct, pct+0.1, d);
}

void main(){
    vec2 st = gl_FragCoord.xy/u_resolution.xy;
    vec3 color = vec3(0.0);

    vec2 pos = vec2(0.5)-st;

    float r = length(pos)*2.0;
    float a = atan(pos.y,pos.x);

    float f = abs(cos(a* 12.)*sin(a* u_time)) *.9+.1;

    float d = distance(r,f);
    float pct = plot(d,0.);
    color = mix(color, vec3(1.0), pct);

    gl_FragColor = vec4(color, 1.0);
}
