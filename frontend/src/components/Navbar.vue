<template>


<nav class="navbar">


<div class="logo">

🌆 Seoul AI

</div>



<div class="menu">


<router-link to="/">
메인
</router-link>



<router-link to="/map">
지도 / 데이터
</router-link>



<router-link to="/community">
커뮤니티
</router-link>


</div>


</nav>


</template>




<style scoped>


.navbar{

position:fixed;

top:0;

left:0;

right:0;


height:80px;


display:flex;

align-items:center;

justify-content:space-between;


padding:0 50px;


background:

rgba(5,8,22,.75);


backdrop-filter:

blur(20px);



border-bottom:

1px solid rgba(255,255,255,.1);



z-index:999;


}




.logo{

font-size:26px;

font-weight:900;

color:white;

}





.menu{

display:flex;

gap:40px;

}





.menu a{

text-decoration:none;

color:#94a3b8;

font-size:16px;

font-weight:bold;

transition:.3s;

}




.menu a:hover{

color:white;

}





.router-link-active{

color:#ffd369 !important;

}




@media(max-width:700px){


.navbar{

padding:0 20px;

}


.menu{

gap:15px;

}


.logo{

font-size:20px;

}


}



</style>