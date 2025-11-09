#ifdef GL_ES
precision mediump float;
#endif

#define PI 3.14159265359

uniform vec2 u_resolution;
uniform float u_time;

mat2 scale(vec2 _scale){
    return mat2(_scale.x,0.0,
                0.0,_scale.y);
}
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
    return  box(_st, vec2(_size,_size/_width)) +
            box(_st, vec2(_size/_width,_size));
}

float plot(float d, float pct){
  return  smoothstep( pct-0.1, pct, d) -
          smoothstep( pct, pct+0.1, d);
}

float circle(vec2 st, vec2 center, float radius, float width)
{
    float r = length(st - center);
    return step(r-width/2.0,radius)-step(r+width/2.0,radius);
}

float rect1(vec2 st, vec2 bottomLeft, vec2 topRight)
{
    st = st - 0.5;
	vec2 inside = step(bottomLeft, st) * step(st, topRight);
    return inside.x * inside.y;
}

float rect2(vec2 st, vec2 size)
{
    st = st - 0.5;
    vec2 halfSize = size * 0.5;
	vec2 inside = step(-halfSize, st) * step(st, halfSize);
    return inside.x * inside.y;
}

float rectOutline(vec2 st, vec2 size, float width)
{
    return rect2(st, size) - rect2(st, size - width * 2.0);
}

void main(){
  vec2 st = gl_FragCoord.xy/u_resolution.xy;
  vec3 color = vec3(0.0);

  // spinning circles thing
  vec2 st1 = st + vec2(0.25,-0.25);

  st1 -= vec2(0.5);
  st1 = scale( vec2(0.5 * sin(u_time) - 3.5) ) * st1;
  st1 += vec2(0.5);

  st1 -= vec2(0.5);
  st1 = rotate2d(-u_time) * st1;
  st1 += vec2(0.5);

  color += vec3(cross(st1,0.8,100.));

  color = mix(color, vec3(1.000,0.392,0.315), circle(st1, vec2(0.5), 0.15, 0.01));
  color = mix(color, vec3(1.000,0.712,0.422), circle(st1, vec2(0.5), 0.25, 0.01));
  color = mix(color, vec3(1.000,0.564,0.631), circle(st1, vec2(0.5), 0.4, 0.01));
  color = mix(color, vec3(1.000,0.747,0.825), circle(st1, vec2(0.5), 0.5, 0.01));

  color = mix(color, vec3(1.), rect1(st1, vec2(0.4), vec2(0.45)));
  color = mix(color, vec3(.9), rectOutline(st + vec2(0.25,-0.25), vec2(.5), 0.01));

  // progress bars
  float progress = abs(sin(0.5 * u_time)) -0.55;
  color = mix(color, vec3(.9), rectOutline(st + vec2(0.,0.15), vec2(1.,.15), 0.01));
  color = mix(color, mix(vec3(0.0,1.0,0.0), vec3(1.0,0.0,0.0), progress + 0.5), rect1(st + vec2(0.,0.2), vec2(-0.48, 0.), vec2(progress,0.1)));

  color = mix(color, vec3(.9), rectOutline(st + vec2(0.,0.35), vec2(1.,.15), 0.01));
  vec2 pos = vec2(0.5)-st;

  color = mix(color, mix(vec3(0.814,0.980,0.704), vec3(0.881,0.490,1.000), -st.x + 2. * abs(sin(0.2 * u_time))), rectOutline(st + vec2(0.,0.35), vec2(.95,.1), 1.));

  gl_FragColor = vec4(color,1.0);
}
