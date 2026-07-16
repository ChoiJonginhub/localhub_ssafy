<script setup>
import { computed } from "vue"
import { useSunsetTheme } from "@/composables/useSunsetTheme.js"

const { sunsetProgress, skyStyle, timeLabel, timeRangeLabel, currentTimeLabel } = useSunsetTheme()

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

Seoul Connect

</h1>



<h2>

서울 관광 & 커뮤니티 플랫폼

</h2>




<p>

관광지를 지도로 탐색하고<br>

커뮤니티에서 인사이트를 공유하는<br>

서울 맞춤 스마트 라이프 가이드

</p>




<div class="controller">
  <div class="controller-title">🌅 Sunset Theme</div>
  <div class="time-inline">
    <span>현재 {{ currentTimeLabel }}</span>
    <span>UI Time : {{ timeRangeLabel }}</span>
  </div>
  <input v-model="sunsetProgress" type="range" min="0" max="100" />
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