  async function countEjemplares() {
    let query = `query countRecords{
                    countSitios
                  }`
            let response = await axios.post("https://especies-siagro.conabio.gob.mx/api", { query: query });
            document.getElementById("ejemplares").textContent=response.data.data.countSitios.toLocaleString('en-US');            

  }

  async function countMaices() {
    let query = `query countRecords{
                    countRegistros
                  }`
            let response = await axios.post("https://maices-siagro.conabio.gob.mx/api/graphql", { query: query });
            document.getElementById("ejemplaresMaices").textContent=response.data.data.countRegistros.toLocaleString('en-US');     
            document.getElementById("maicesbases").textContent=response.data.data.countRegistros.toLocaleString('en-US');         

  }

  async function countEspecies() {
    let query = `query countRecords{
                  countTaxons
                  }`
            let response = await axios.post("https://especies-siagro.conabio.gob.mx/api", { query: query });
            document.getElementById("especies").textContent=response.data.data.countTaxons.toLocaleString('en-US');                   
            document.getElementById("especiesAgro").textContent=response.data.data.countTaxons.toLocaleString('en-US');   

  }

  async function countReg() {
    let query = `query countRecords{
                countManejos
                  }`
            let response = await axios.post("https://colectas-siagro.conabio.gob.mx/api/graphql", { query: query });
            document.getElementById("reg").textContent=response.data.data.countManejos.toLocaleString('en-US');     
            document.getElementById("regcol").textContent=response.data.data.countManejos.toLocaleString('en-US');               

  }
  
  async function countAlimentos() {
    let query = `query countRecords{
                    countAlimentos
                }`
            let response = await axios.post("https://canastas-siagro.conabio.gob.mx/api/graphql", { query: query });
            document.getElementById("alimentos").textContent=response.data.data.countAlimentos.toLocaleString('en-US');      
            document.getElementById("alimentosCa").textContent=response.data.data.countAlimentos.toLocaleString('en-US');               

  }

  async function countRegiones() {
    let query = `query countRecords{
      countProyectos
                }`
            let response = await axios.post("https://canastas-siagro.conabio.gob.mx/api/graphql", { query: query });
            document.getElementById("regiones").textContent=response.data.data.countProyectos.toLocaleString('en-US');                

  }

  async function countRegistros() {
    let query = `query countRecords{
                    countRegistros
                }`
            let response = await axios.post("https://nutricion-siagro.conabio.gob.mx/api/graphql", { query: query });  
            document.getElementById("registros").textContent=response.data.data.countRegistros.toLocaleString('en-US');  
            document.getElementById("registrosNutri").textContent=response.data.data.countRegistros.toLocaleString('en-US');                    

  }

  async function countConsumidas() {
    let query = `query countRecords{
                    countTaxons
                }`
            let response = await axios.post("https://focales-siagro.conabio.gob.mx/api/graphql", { query: query });
            document.getElementById("consumidas").textContent=response.data.data.countTaxons.toLocaleString('en-US');       
            document.getElementById("especiesge").textContent=response.data.data.countTaxons.toLocaleString('en-US');                

  }

  async function getStatus() {
      var labels=[];
      var total=[];

    let query = `query countRecords{
                    registros(pagination:{limit:6000}){
                    EstatusEcologico
                    }
                }`
            let response = await axios.post("https://colectas-siagro.conabio.gob.mx/api/graphql", { query: query });
            edges=response.data.data.registros;
            size=Object.keys(edges).length;
            //console.log(size); 
            for(var i=0;i<size;i++){
                estatus=edges[i].EstatusEcologico;
                total.push(estatus);
                if(!labels.includes(estatus)){
                    labels.push(estatus);
                }
            }

            const count = {};

            for (const element of total) {
              if (count[element]) {
                count[element] += 1;
              } else {
                count[element] = 1;
              }
            }

            //console.log(count);
            //console.log(Object.values(count));
            dataArray=Object.values(count);
            //let prueba=getStatus().then(console.log);

            var ctxh = document.getElementById("chart2");
                  var chart2 = new Chart(ctxh, {
                    type: 'bar',
                data: {
                  labels: labels,
                  datasets: [
                    {
                      label: "Número de registros",
                      backgroundColor: ["#c45850", "#e8c3b9","#3cba9f","#e8c3b9","#c45850"],
                      data: dataArray
                    }
                  ]
                },
                options: {
                  legend: { display: false },
                  title: {
                    display: true,
                    text: 'Estatus ecológico',
                    fontSize: 18
                  }
                }
            });

            //return labels;   

  }

  async function getManejos() {
    var labels=[];
    var total=[];
    var aux=[];
  let query = `query countRecords{
                  manejos(pagination:{limit:6000}, search:{field:TipoManejo,value:null,operator:not}){
                    TipoManejo
                  }
                }`
          let response = await axios.post("https://colectas-siagro.conabio.gob.mx/api/graphql", { query: query });
          edges=response.data.data.manejos;
          size=Object.keys(edges).length;
          //console.log(size); 
          for(var i=0;i<size;i++){
              manejo=edges[i].TipoManejo;
              aux=manejo.split("; ");
              //console.log(aux);
              if(aux.length>1){
                for(var j=0;j<aux.length;j++){
                  manejo=aux[j];
                  total.push(manejo);
                  if(!labels.includes(manejo)){
                    labels.push(manejo);
                  }
                }
              }
              else{
                total.push(manejo);
                if(!labels.includes(manejo)){
                    labels.push(manejo);
                }
              }
              
          }

          //console.log(labels,total);

          const count = {};

          for (const element of total) {
            if (count[element]) {
              count[element] += 1;
            } else {
              count[element] = 1;
            }
          }

          //console.log(count);
          //console.log(Object.values(count));
          dataArray=Object.values(count);
          //let prueba=getStatus().then(console.log);

          var ctx = document.getElementById("chart1");
          var chart1 = new Chart(ctx, {
            type: 'bar',
        data: {
          labels: labels,
          datasets: [
            {
              label: "Número de registros",
              backgroundColor: ["#3e95cd", "#8e5ea2","#3cba9f","#e8c3b9","#c45850","#A1C349"],
              data: dataArray
            }
          ]
        },
        options: {
          legend: { display: false },
          title: {
            display: true,
            text: 'Tipo de manejo',
            fontSize: 18
          }
        }
    });

          //return labels;   

}

  async function countGeneros() {
    var edges;
    var gen;
    var auxArr=[];

     
        let query = `query getTaxons{
                            etiqueta_agrobds(pagination:{limit:3000}){
                                agro_id
                            }
                    }`
                    //console.log(query);
        try{
            let response = await axios.post("https://especies-siagro.conabio.gob.mx/api", { query: query });
            edges = response.data.data.etiqueta_agrobds;  
            size=Object.keys(edges).length;
            for(var i=0; i<=size; i++){
                query = `query getTaxons{
                            etiqueta_agrobds(pagination:{limit:1},search:{field:agro_id, value:"${edges[i].agro_id}", operator:eq}){
                            
                            Taxon{
                                Genero
                            }
                            }
                        }`
                        //console.log(query);
                        response = await axios.post("https://especies-siagro.conabio.gob.mx/api", { query: query });
                        gen=response.data.data.etiqueta_agrobds[0].Taxon.Genero;
                        console.log(gen);
                        if(!auxArr.includes(gen)){
                            auxArr.push(gen);
                        }
                        
            }
            
        }catch{
            console.log("nop");
        }
            
    //console.log(auxArr.length);
            document.getElementById("generos").textContent=auxArr.length; 
            document.getElementById("generosAgro").textContent=auxArr.length;           

  }
  

/*
  function count(){
    var counter = { var: 0 };
    TweenMax.to(counter, 3, {
      var: 100, 
      onUpdate: function () {
        var number = Math.ceil(counter.var);
        $('.counter').html(number);
        if(number === counter.var){ counter.kill(); }
      },
      onComplete: function(){
        count();
      },    
      ease:Circ.easeOut
    });
  }*/
  
  
