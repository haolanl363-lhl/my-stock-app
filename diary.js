// =============================
// Investment Journal 日记系统
// =============================



let diaries =
JSON.parse(
localStorage.getItem("investment_diary")
)
|| [];



let market = "";

let emotion = "";




// 显示日期


function showDate(){


let now =
new Date();


let date =
now.getFullYear()
+
"-"
+
String(now.getMonth()+1).padStart(2,"0")
+
"-"
+
String(now.getDate()).padStart(2,"0");



document.getElementById("date")
.innerHTML=date;



}



showDate();






// 选择市场


function selectMarket(btn){



document
.querySelectorAll(
".market-select button"
)
.forEach(
b=>b.classList.remove("selected")
);



btn.classList.add("selected");


market=btn.innerText;


}








// 选择情绪


function selectEmotion(btn){



document
.querySelectorAll(
".emotion button"
)
.forEach(
b=>b.classList.remove("selected")
);



btn.classList.add("selected");


emotion=btn.innerText;


}









// 保存日记


function saveDiary(){



let event =
document.getElementById("event")
.value;



let trade =
document.getElementById("trade")
.value;



let mistake =
document.getElementById("mistake")
.value;



let lesson =
document.getElementById("lesson")
.value;



let rule =
document.getElementById("rule")
.value;





if(
!event &&
!trade &&
!mistake
){


alert(
"请至少填写一点内容"
);


return;


}





let diary={


id:Date.now(),


date:
document.getElementById("date")
.innerText,


market,


emotion,


event,


trade,


mistake,


lesson,


rule



};






diaries.unshift(diary);



localStorage.setItem(

"investment_diary",

JSON.stringify(diaries)

);



clearInput();


renderDiary();



alert(
"今日复盘已保存"
);



}









// 清空输入


function clearInput(){



document
.querySelectorAll(
"textarea"
)
.forEach(
item=>item.value=""
);



}










// 显示时间轴


function renderDiary(){



let box =
document.getElementById(
"diaryList"
);



box.innerHTML="";





diaries.forEach(
item=>{


box.innerHTML += `



<div class="diary-item">


<div class="time">

${item.date}

</div>



<h3>

${item.market || "今日市场"}

${item.emotion || ""}

</h3>




<p>

<b>
今天发生：
</b>

<br>

${item.event || "无"}

</p>




<p>

<b>
我的交易：
</b>

<br>

${item.trade || "无"}

</p>





<p>

<b>
错误复盘：
</b>

<br>

${item.mistake || "无"}

</p>






<p>

<b>
今日领悟：
</b>

<br>

${item.lesson || "无"}

</p>





<p>

<b>
新的纪律：
</b>

<br>

${item.rule || "无"}

</p>





<button

class="delete"

onclick="deleteDiary(${item.id})"

>

删除

</button>




</div>



`;



});




}









// 删除


function deleteDiary(id){



diaries =

diaries.filter(

item=>

item.id!==id

);



localStorage.setItem(

"investment_diary",

JSON.stringify(diaries)

);



renderDiary();



}








// 页面启动


window.onload=function(){


showDate();


renderDiary();


}
