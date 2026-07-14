<script setup>


import {
ref,
onMounted,
onBeforeUnmount
} from "vue"



const category="seoul"
  


const posts=ref([])


const loading=ref(false)


const errorMessage=ref("")


const successMessage=ref("")


const notificationMessage=ref("")



const showWrite=ref(false)



const editingId=ref(null)



const deletePasswords=ref({})



const onlineCount=ref(0)



const socket=ref(null)


const reconnectTimer=ref(null)



const form=ref({

title:"",

content:"",

password:""

})




async function fetchPosts(){


try{


loading.value=true



const res =
await fetch(
`http://localhost:8000/api/boards/${category}/posts`
)



posts.value =
await res.json()



}

catch(err){


errorMessage.value=err.message


}

finally{


loading.value=false


}


}




function resetForm(){


editingId.value=null


form.value={

title:"",

content:"",

password:""

}


}





function startEdit(post){


showWrite.value=true


editingId.value=post.id



form.value={


title:post.title,


content:post.content,


password:""


}



}





async function submitForm(){



if(
!form.value.title ||
!form.value.content ||
!form.value.password
){

errorMessage.value=
"제목, 내용, 비밀번호를 입력해주세요."

return

}




let url =
`http://localhost:8000/api/boards/${category}/posts`



let method="POST"



if(editingId.value){


url+=`/${editingId.value}`

method="PUT"


}



try{


const res =
await fetch(url,{


method,


headers:{


"Content-Type":"application/json"


},


body:

JSON.stringify(form.value)



})



if(!res.ok)
throw new Error("처리 실패")




successMessage.value=

editingId.value

?"게시글 수정 완료"

:"게시글 등록 완료"



resetForm()


showWrite.value=false


fetchPosts()



}

catch(err){


errorMessage.value=err.message


}


}







async function deletePost(id){



const password =
deletePasswords.value[id]



if(!password){

errorMessage.value=
"삭제 비밀번호 입력"

return

}




try{


const res =
await fetch(

`http://localhost:8000/api/boards/${category}/posts/${id}`,

{


method:"DELETE",


headers:{

"Content-Type":"application/json"

},


body:

JSON.stringify({

password

})


}

)



if(!res.ok)
throw new Error("삭제 실패")



fetchPosts()



}


catch(err){


errorMessage.value=err.message


}



}





function connectSocket(){


socket.value =
new WebSocket(

`ws://localhost:8000/ws/notifications?client_id=${Date.now()}`

)




socket.value.onmessage=(e)=>{


const data =
JSON.parse(e.data)



if(data.type==="presence"){


onlineCount.value=data.count


}




if(data.type==="new_post"){


posts.value.unshift(data.post)



notificationMessage.value=

"새 게시글이 등록되었습니다."


}



}





socket.value.onclose=()=>{


reconnectTimer.value=

setTimeout(

connectSocket,

1000

)


}



}




onMounted(()=>{


fetchPosts()


connectSocket()


})




onBeforeUnmount(()=>{


if(socket.value)

socket.value.close()



if(reconnectTimer.value)

clearTimeout(reconnectTimer.value)



})



</script>






<template>



<div class="community">



<header>

<br>
<br>
<br>
<br>
<h1>

Community

</h1>
<p>

서울 시민들의 실시간 커뮤니티

</p>



<button

class="plus"

@click="showWrite=true"

>

+

</button>



</header>






<!-- 작성 패널 -->


<div
v-if="showWrite"
class="modal"
>

  <div class="modal-card">

    <button
      class="close-btn"
      @click="showWrite=false"
    >
      ✕
    </button>

    <h2>
      {{ editingId ? "게시글 수정" : "게시글 작성" }}
    </h2>

    <input
      v-model="form.title"
      placeholder="제목"
    />

    <textarea
      v-model="form.content"
      rows="8"
      placeholder="내용"
    />

    <input
      v-model="form.password"
      type="password"
      placeholder="수정 / 삭제 비밀번호"
    />

    <div class="modal-buttons">

      <button
        class="cancel"
        @click="showWrite=false"
      >
        취소
      </button>

      <button
        class="submit"
        @click="submitForm"
      >
        등록하기
      </button>

    </div>

  </div>

</div>




<div class="status">

현재 접속자

<b>

{{onlineCount}}

</b>

명

</div>






<p v-if="loading">

불러오는 중...

</p>



<p class="error">

{{errorMessage}}

</p>



<p class="success">

{{successMessage}}

</p>





<div class="notice">

{{notificationMessage}}

</div>







<article

v-for="post in posts"

:key="post.id"

class="post"

>



<h2>

{{post.title}}

</h2>



<p>

{{post.content}}

</p>



<div class="buttons">


<button

@click="startEdit(post)"

>

수정

</button>




<input

v-model="deletePasswords[post.id]"

type="password"

placeholder="삭제 비밀번호"

/>



<button

class="delete"

@click="deletePost(post.id)"

>

삭제

</button>



</div>




</article>



</div>



</template>






<style scoped>



.community{


min-height:100vh;


padding:40px;


background:

linear-gradient(
180deg,
#050816,
#111827
);


color:white;


}



header{

margin-bottom:60px;

text-align:center;

position:relative;

}

header h1{

font-size:80px;

font-weight:900;

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



h1{

font-size:48px;

}



.plus{

position:fixed;

right:40px;

bottom:950px;

width:70px;

height:70px;

border-radius:50%;

font-size:34px;

background:linear-gradient(
135deg,
#ffd369,
#ff8a00
);

box-shadow:
0 20px 40px rgba(255,180,0,.35);

z-index:100;

}


.modal{

position:fixed;

inset:0;

background:rgba(0,0,0,.45);

backdrop-filter:blur(12px);

display:flex;

justify-content:center;

align-items:center;

z-index:999;

animation:fade .25s;

}

.modal-card{

width:650px;

max-width:92%;

padding:40px;

border-radius:35px;

background:rgba(255,255,255,.08);

border:1px solid rgba(255,255,255,.12);

backdrop-filter:blur(35px);

box-shadow:

0 30px 80px rgba(0,0,0,.45);

position:relative;

animation:popup .3s;

}

.close-btn{

position:absolute;

top:20px;

right:20px;

width:42px;

height:42px;

border-radius:50%;

background:rgba(255,255,255,.08);

color:white;

font-size:18px;

}

.modal-card h2{

margin-bottom:30px;

font-size:34px;

font-weight:800;

}

.modal-card input,

.modal-card textarea{

width:100%;

margin-bottom:18px;

padding:18px;

border-radius:18px;

background:rgba(255,255,255,.05);

border:1px solid rgba(255,255,255,.12);

color:white;

font-size:16px;

outline:none;

transition:.25s;

}

.modal-card input:focus,

.modal-card textarea:focus{

border-color:#7c4dff;

box-shadow:

0 0 25px rgba(124,77,255,.35);

}

.modal-buttons{

display:flex;

justify-content:flex-end;

gap:15px;

margin-top:15px;

}

.cancel{

background:rgba(255,255,255,.08);

color:white;

}

.submit{

background:linear-gradient(
135deg,
#7c4dff,
#ec4899
);

color:white;

}

@keyframes popup{

from{

opacity:0;

transform:translateY(30px) scale(.95);

}

to{

opacity:1;

transform:translateY(0) scale(1);

}

}

@keyframes fade{

from{

opacity:0;

}

to{

opacity:1;

}

}


input,
textarea{

background:

rgba(255,255,255,.06);

border:

1px solid rgba(255,255,255,.08);

backdrop-filter:blur(20px);

color:white;

padding:18px;

border-radius:18px;

}



button{

border:none;

padding:14px 28px;

border-radius:18px;

cursor:pointer;

font-weight:700;

background:

linear-gradient(

135deg,

#ffd369,

#ffb347

);

transition:.3s;

}

button:hover{

transform:

translateY(-3px);

box-shadow:

0 10px 25px rgba(255,180,0,.35);

}



.close{

margin-left:10px;

background:#64748b;

}



.post{

padding:35px;

border-radius:30px;

background:

rgba(255,255,255,.07);

border:

1px solid rgba(255,255,255,.08);

backdrop-filter:blur(25px);

transition:.35s;

}

.post:hover{

transform:

translateY(-8px);

border-color:#ffd369;

background:

rgba(255,255,255,.12);

}



.buttons{


display:flex;

gap:10px;

margin-top:20px;


}



.delete{

background:#ef4444;

color:white;

}


.status{

display:inline-block;

padding:14px 28px;

border-radius:999px;

background:

rgba(255,255,255,.08);

border:

1px solid rgba(255,255,255,.1);

backdrop-filter:blur(20px);

margin:40px 0;

}



.error{

color:#fb7185;

}



.success{

color:#4ade80;

}



</style>