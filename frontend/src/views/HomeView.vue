<script setup>

import { ref, computed } from "vue"


const sunsetProgress = ref(50)



const gradients = [
  ["#ff9a44", "#fc6076", "#ff5858"],
  ["#ff7eb3", "#7c4dff", "#5e60ce"],
  ["#3b82f6", "#1e3a8a", "#020617"]
]

function lerp(a, b, t) {
  return a + (b - a) * t
}

function hexToRgb(hex) {
  const n = parseInt(hex.slice(1), 16)

  return {
    r: (n >> 16) & 255,
    g: (n >> 8) & 255,
    b: n & 255
  }
}

function rgbToHex({ r, g, b }) {
  return (
    "#" +
    [r, g, b]
      .map(v =>
        Math.round(v)
          .toString(16)
          .padStart(2, "0")
      )
      .join("")
  )
}

function mix(c1, c2, t) {

  const a = hexToRgb(c1)
  const b = hexToRgb(c2)

  return rgbToHex({

    r: lerp(a.r, b.r, t),
    g: lerp(a.g, b.g, t),
    b: lerp(a.b, b.b, t)

  })

}

const skyStyle = computed(() => {

  const p = sunsetProgress.value / 100

  const idx = p < 0.5 ? 0 : 1

  const t = p < 0.5 ? p * 2 : (p - 0.5) * 2

  const colors = gradients[idx].map((c, i) =>
    mix(c, gradients[idx + 1][i], t)
  )

  return {

    background: `
radial-gradient(circle at 20% 20%, ${colors[0]}55, transparent 40%),
radial-gradient(circle at 80% 30%, ${colors[1]}66, transparent 45%),
radial-gradient(circle at 50% 80%, ${colors[2]}66, transparent 45%),
linear-gradient(135deg,
${colors[0]},
${colors[1]},
${colors[2]})
`,

    backgroundSize: "300% 300%",
    backgroundPosition: `${sunsetProgress.value}% 50%`

  }

})




</script>



<template>


<div
class="home"
:style="skyStyle"
>


<div class="glow glow1"></div>

<div class="glow glow2"></div>



<section class="hero">



<div class="badge">

🌐 SMART CITY PLATFORM

</div>




<h1>

Seoul AI

</h1>



<h2>

미래 도시 데이터 플랫폼

</h2>




<p>

도시 데이터를 분석하고<br>

지도와 시민 커뮤니티를 연결하는<br>

서울형 스마트 시티 플랫폼

</p>




<div class="controller">


<div class="controller-title">

🌅 Sunset Theme

</div>



<input

v-model="sunsetProgress"

type="range"

min="0"

max="100"

/>



<div class="time">

<span>
17:20
</span>


<span>
20:40
</span>

</div>



</div>






<div class="cards">



<div class="card">


<div class="icon">

🗺

</div>


<h3>

지도 데이터

</h3>


<p>

서울 공간 데이터를<br>
실시간 시각화

</p>


</div>





<div class="card">


<div class="icon">

📊

</div>


<h3>

데이터 분석

</h3>


<p>

도시 데이터를 기반으로<br>
새로운 인사이트 제공

</p>


</div>





<div class="card">


<div class="icon">

💬

</div>


<h3>

시민 커뮤니티

</h3>


<p>

서울 시민들의<br>
실시간 소통 공간

</p>


</div>



</div>




</section>



</div>



</template>





<style scoped>


.home{


min-height:calc(100vh - 80px);


display:flex;


justify-content:center;


align-items:center;


overflow:hidden;


position:relative;


color:white;


transition:1s;


}





.hero{


width:100%;


max-width:1100px;


text-align:center;


padding:40px;



z-index:2;


}





.badge{


display:inline-block;


padding:10px 20px;


border-radius:999px;


background:

rgba(255,255,255,.08);



border:

1px solid rgba(255,255,255,.15);



backdrop-filter:

blur(20px);



font-size:14px;


letter-spacing:2px;


margin-bottom:35px;


}




h1{


font-size:110px;


font-weight:900;


letter-spacing:-5px;


margin:0;



background:

linear-gradient(

135deg,

#fff,

#ffd369,

#93c5fd

);



-webkit-background-clip:text;


color:transparent;



}




h2{


font-size:38px;


margin:20px 0;


font-weight:700;


}




p{


font-size:20px;


line-height:1.8;


color:#cbd5e1;


}





.controller{


width:520px;


max-width:100%;


margin:50px auto;


padding:30px;



border-radius:30px;


background:

rgba(255,255,255,.08);



border:

1px solid rgba(255,255,255,.15);



backdrop-filter:

blur(25px);



box-shadow:

0 20px 60px rgba(0,0,0,.3);



}





.controller-title{


font-size:18px;


margin-bottom:20px;


}




input{


width:100%;


}




.time{


display:flex;


justify-content:space-between;


margin-top:15px;


color:#94a3b8;


}




.cards{


display:flex;


justify-content:center;


gap:30px;


margin-top:40px;


}




.card{


width:280px;


padding:35px;



border-radius:32px;



background:

rgba(255,255,255,.08);



border:

1px solid rgba(255,255,255,.12);



backdrop-filter:

blur(25px);



transition:.4s;



}





.card:hover{


transform:

translateY(-15px);


background:

rgba(255,255,255,.15);



}




.icon{


font-size:50px;


margin-bottom:20px;


}




.card h3{


font-size:25px;


}



.card p{


font-size:16px;


}





.glow{


position:absolute;


border-radius:50%;


filter:blur(100px);


opacity:.35;


}




.glow1{


width:400px;

height:400px;


background:#6366f1;


top:-100px;


left:-100px;


}



.glow2{


width:500px;

height:500px;


background:#ec4899;


bottom:-200px;


right:-150px;


}





@media(max-width:900px){


h1{

font-size:70px;

}


.cards{

flex-direction:column;

align-items:center;

}



}



</style>