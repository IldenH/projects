#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 u_resolution;
uniform float u_time;

#define PI 3.141592654
#define TWO_PI 6.283185307

vec2 rotate2D(vec2 _st, float _angle){
    _st -= 0.5;
    _st =  mat2(cos(_angle),-sin(_angle),
                sin(_angle),cos(_angle)) * _st;
    _st += 0.5;
    return _st;
}

vec2 tile(vec2 _st, float _zoom){
    _st *= _zoom;
    return fract(_st);
}

float box(vec2 _st, vec2 _size, float _smoothEdges){
    _size = vec2(0.5)-_size*0.5;
    vec2 aa = vec2(_smoothEdges*0.5);
    vec2 uv = smoothstep(_size,_size+aa,_st);
    uv *= smoothstep(_size,_size+aa,vec2(1.0)-_st);
    return uv.x*uv.y;
}

float boxOutline(vec2 _st, vec2 _size, float _width, float _smoothEdges){
    return box(_st, _size, _smoothEdges) - box(_st, _size * _width, _smoothEdges);
}

// http://thndl.com/square-shaped-shaders.html
// https://thebookofshaders.com/07
float shape(vec2 _st, int N, float _size){
  float d = 0.0;

  // Remap the space to -1. to 1.
  _st = _st *2.-1.;

  // Angle from the current pixel
  float a = atan(_st.x,_st.y)+PI;

  // Angular spacing between vertices of shape
  float r = TWO_PI/float(N);

  // Shaping function that modulate the distance
  d = cos(floor(.5+a/r)*r-a)*length(_st);

  float color = 1.0-smoothstep(_size,_size + _size * 0.01,d);
  return color;
}

float shapeOutline(vec2 _st, int N, float _size, float _width){
    return shape(_st, N, _size) - shape(_st, N, _size * _width);
}
void main(void){
    vec2 st0 = gl_FragCoord.xy/u_resolution.xy;
    vec3 color = vec3(0.0);

	vec2 st = tile(st0,4.);

	color = mix(color, vec3(st0,0.5), shapeOutline(st, 8, 1.,0.9));

    gl_FragColor = vec4(color,1.0);
}
