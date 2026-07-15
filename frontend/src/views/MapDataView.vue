<script setup>

import MapView from "@/components/MapView.vue"
import Dashboard from "@/components/Dashboard.vue"

</script>



<template>


<div class="page">

<br>
<br>
<br>
<h1>
지도 및 데이터 시각화
</h1>


<p class="desc">
서울 지역 관광 데이터 및 위치 정보를 확인합니다.
</p>



<MapView />


<Dashboard />

</div>


</template>




<style scoped>




h1{

font-size:48px;

font-weight:900;

}



.desc{

color:#94a3b8;

margin-bottom:40px;

}



</style>