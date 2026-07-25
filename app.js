// =======================
// 投资错题本 Pro 核心程序
// =======================



let mistakes = JSON.parse(
localStorage.getItem("mistakes")
) || [];




// 初始化图表

let chart;



function initChart(){


let ctx =
document
.getElementById("mistakeChart")
.getContext("2d");



chart = new Chart(ctx,{

type:"line",


data:{


labels:[

"1月",
"2月",
"3月",
"4月",
"5月",
"6月"

],



datasets:[{


label:"投资错误次数",


data:[

2,
4,
3,
7,
5,
mistakes.length

],



borderWidth:3,


tension:.4


}]


},



options:{


responsive:true,


plugins:{


legend:{


display:false


}


}


}



});


}









// 添加错误


function addMistake(){



let stock =
document.getElementById("stock").value;


let loss =
document.getElementById("loss").value;



let category =
document.getElementById("category").value;



let reason =
document.getElementById("reason").value;



let mistake =
document.getElementById("mistake").value;



let lesson =
document.getElementById("lesson").value;



if(!stock){


alert("请输入股票名称");


return;


}




let item={


id:Date.now(),


stock,


loss:Number(loss)||0,


category,


reason,


mistake,


lesson,


date:new Date()
.toLocaleDateString()


};



mistakes.unshift(item);



save();


render();


clearForm();


}







// 保存


function save(){


localStorage.setItem(

"mistakes",

JSON.stringify(mistakes)

);


}







// 清空输入


function clearForm(){


document
.querySelectorAll(
"input,textarea"
)
.forEach(e=>{


if(e.type!="checkbox"){

e.value="";

}


});


}







// 页面刷新显示


function render(){


let list =
document.getElementById("list");



list.innerHTML="";



let totalLoss=0;



mistakes.forEach(item=>{


totalLoss += item.loss;




list.innerHTML +=`



<div class="mistake-item">



<h3>

${item.stock}

</h3>



<span class="tag">

${item.category}

</span>



<p>

📅 ${item.date}

</p>



<p>

亏损：

<span class="danger">

¥${item.loss}

</span>

</p>



<p>

<b>
当时想法：
</b>

<br>

${item.reason || "未填写"}

</p>




<p>

<b>

错误原因：

</b>

<br>

${item.mistake || "未填写"}

</p>




<p>

<b>

以后改进：

</b>

<br>

${item.lesson || "未填写"}

</p>




<button 

class="delete"

onclick="deleteMistake(${item.id})">


删除记录


</button>




</div>


`;



});






document
.getElementById(
"totalMistake"
)
.innerHTML =
mistakes.length;




document
.getElementById(
"totalLoss"
)
.innerHTML =
"¥"+totalLoss;




updateScore();



}









// 删除


function deleteMistake(id){



mistakes =
mistakes.filter(
item=>item.id!==id
);



save();


render();


}








// 搜索


function searchMistake(){



let keyword =
document
.getElementById("search")
.value
.toLowerCase();



let items =
document
.querySelectorAll(
".mistake-item"
);



items.forEach(item=>{


if(
item.innerText
.toLowerCase()
.includes(keyword)
){


item.style.display="block";


}else{


item.style.display="none";


}


});


}








// 投资能力评分


function updateScore(){



let score=100;



score -= mistakes.length*2;



if(score<20){

score=20;

}



document
.getElementById("score")
.innerHTML =
score;


}









// 启动


window.onload=function(){


initChart();


render();


  }
