import { createRouter, createWebHistory } from 'vue-router'

import HomeView from '../views/HomeView.vue'
import MapDataView from '../views/MapDataView.vue'
import CommunityView from '../views/CommunityView.vue'
import MeetupView from '../views/MeetupView.vue'


const router=createRouter({

history:createWebHistory(),

routes:[

{
path:"/",
component:HomeView
},

{
path:"/map",
component:MapDataView
},

{
path:"/community",
component:CommunityView
},
{
path:"/meetups",
component:MeetupView
}

]

})


export default router