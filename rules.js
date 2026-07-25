// ============================
// 投资原则库系统
// ============================


let rules = JSON.parse(

localStorage.getItem("investment_rules")

) || [];






// 添加原则


function addRule(){



let title =

document.getElementById("title").value;



let type =

document.getElementById("type").value;



let level =

document.getElementById("level").value;



let content =

document.getElementById("content").value;





if(!title){


alert("请输入原则名称");


return;


}





let rule = {


id:Date.now(),


title,


type,


level,


content,


date:new Date()
.toLocaleDateString()



};





rules.unshift(rule);



saveRules();



renderRules();



clearForm();



}









// 保存


function saveRules(){


localStorage.setItem(

"investment_rules",

JSON.stringify(rules)

);


}









// 清空输入


function clearForm(){


document
.querySelectorAll(
"input,textarea"
)
.forEach(
item=>item.value=""
);


}









// 显示原则


function renderRules(){



let box =

document.getElementById("rules");



box.innerHTML="";





rules.forEach(rule=>{



box.innerHTML += `



<div class="rule-item">


<h3>

${rule.title}

</h3>



<span class="category">

${rule.type}

</span>



<div class="level">

${rule.level}

</div>




<p class="content">

${rule.content || "暂无说明"}

</p>



<p>

创建时间：

${rule.date}

</p>




<button

class="delete"

onclick="deleteRule(${rule.id})"

>

删除原则

</button>




</div>



`;



});



}









// 删除


function deleteRule(id){



rules =

rules.filter(

item => item.id !== id

);



saveRules();


renderRules();


}








// 初始化


window.onload=function(){


renderRules();


}
