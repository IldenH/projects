#ifdef GL_ES
precision mediump float;
#endif

#define PI 3.141592

uniform vec2 u_resolution;
uniform float u_time;

mat2 rotate2d(float _angle){
    return mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle));
}

float box(in vec2 _st, in vec2 _size){
    _size = vec2(0.5) - _size*0.5;
    vec2 uv = smoothstep(_size,
                        _size+vec2(0.001),
                        _st);
    uv *= smoothstep(_size,
                    _size+vec2(0.001),
                    vec2(1.0)-_st);
    return uv.x*uv.y;
}

float cross(in vec2 _st, float _size, float _width){
	_st -= vec2(0.5);
	_st *= rotate2d(0.8);
	_st += vec2(0.5);
    return  box(_st, vec2(_size,_size/_width)) +
            box(_st, vec2(_size/_width,_size));
}

float circle(in vec2 _st, in float _radius){
    vec2 l = _st-vec2(0.5);
    return 1.-smoothstep(_radius-(_radius*0.01),
                         _radius+(_radius*0.01),
                         dot(l,l)*4.0);
}

float circleOutline(in vec2 _st, in float _radius, in float _width){
    return circle(_st, _radius) - circle(_st, _radius - _width);
}

vec2 grid(in vec2 _st, in vec2 _grid){
  _st *= _grid;
  _st = fract(_st);
  return _st;
}

void main() {
  vec2 st0 = gl_FragCoord.xy/u_resolution;
  vec3 color = vec3(0.157);

  vec2 st = grid(st0, vec2(3.0));
  st0 *= 3.;

  float circles = max(max(step(st0.x,1.)*step(2.,st0.y),step(2.,st0.x)*step(1.,st0.y)), step(1.,st0.x)*step(st0.x,2.)*step(st0.y,1.));
  float crosses = (1.0 - circles);

  float toggle = step(0., sin(u_time));

  float maskCircle = (circles * toggle) + (crosses * (1.0 - toggle));
  float maskCross = (crosses * toggle) + (circles * (1.0 - toggle));

  color = mix(color, vec3(0.514, 0.647, 0.596), step(0.5, maskCircle * circleOutline(st,0.5,0.2)));
  color = mix(color, vec3(0.984, 0.286, 0.204), step(0.5, maskCross * cross(st,0.1,0.1)));

  gl_FragColor = vec4(color,1.0);
}
