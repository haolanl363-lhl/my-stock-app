// ==============================
// 投资原则库功能
// rules.js
// ==============================


// 获取已经保存的数据

let rules = JSON.parse(
    localStorage.getItem("investment_rules")
) || [];




// 添加投资原则

function addRule(){

    let title = document.getElementById("title").value;

    let type = document.getElementById("type").value;

    let level = document.getElementById("level").value;

    let content = document.getElementById("content").value;



    if(title.trim() === ""){

        alert("请输入原则名称");

        return;

    }



    let newRule = {

        id: Date.now(),

        title:title,

        type:type,

        level:level,

        content:content,

        date:new Date().toLocaleDateString()

    };



    rules.unshift(newRule);



    saveRules();


    renderRules();


    clearInput();


}







// 保存数据

function saveRules(){

    localStorage.setItem(

        "investment_rules",

        JSON.stringify(rules)

    );

}








// 显示原则卡片

function renderRules(){


    let box = document.getElementById("rules");


    if(!box){

        return;

    }


    box.innerHTML = "";



    rules.forEach(item=>{


        box.innerHTML += `


        <div class="rule-item">


            <h2>${item.title}</h2>


            <div class="tag">

            ${item.type}

            </div>



            <h4>

            重要等级：

            ${item.level}

            </h4>



            <p>

            ${item.content}

            </p>



            <small>

            创建时间：

            ${item.date}

            </small>



            <br>


            <button onclick="deleteRule(${item.id})">

            删除

            </button>


        </div>


        `;


    });



}








// 删除原则


function deleteRule(id){


    rules = rules.filter(

        item => item.id !== id

    );


    saveRules();


    renderRules();


}








// 清空输入框


function clearInput(){


    document.getElementById("title").value="";


    document.getElementById("content").value="";


}








// 页面打开自动加载


window.onload=function(){


    renderRules();


};
